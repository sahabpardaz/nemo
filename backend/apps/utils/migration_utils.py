import re
from abc import ABC, abstractmethod
from django.db import migrations, connection
from django.contrib.contenttypes.models import ContentType
from apps.utils.general_utils import StringTuple, MultipleStrings, convert_names_to_tuple


def _objects_have_same_field_values(obj1, obj2, fields: StringTuple):
    if (obj1 is None) != (obj2 is None):
        return False
    return all(getattr(obj1, f) == getattr(obj2, f) for f in fields)


class AbstractStringUnificationOperation(migrations.RunPython, ABC):
    """
    Abstract database migration operation to make a string field have unique values.

    This operation is mainly used before adding a unique constraint on the corresponding field.

    If 'with_respect_to' is specified, then the 'field' is unified within that scope.
    In other words, (field, *with_respoect_to_fields) will form a unique key.

    When undoing the operation, the field is modified only when 'enable_revert' is True.
    """

    @abstractmethod
    def unify_value(self, value: str, occurrence_number: int, obj) -> str:
        """
        Creates a (hopefully) unified version of a string.

        Parameters:
            value (str): The string value that needs unification
            occurrence_number (int): #occurance of the given value
            obj: The object to which the value belongs

        Returns:
            str: The string value after unification.
        """
        pass

    @abstractmethod
    def revert_unified_value(self, value: str, obj) -> str:
        pass

    def _get_model_queryset(self, apps, schema_editor):
        return apps.get_model(self.app, self.model).objects.using(schema_editor.connection.alias)

    def _get_iterator(self, queryset):
        return queryset.iterator(chunk_size=self.processing_chunk_size)

    def _unify_field(self, apps, schema_editor):
        """Perform field unification"""
        all_fields_to_unify = (*self.with_respect_to_fields, self.field,)
        iteration_order = (*all_fields_to_unify, *self.unification_ordering, 'pk',)
        cluster_representative = None
        occurrence_number: int = 0
        for obj in self._get_iterator(self._get_model_queryset(apps, schema_editor).order_by(*iteration_order)):
            if not _objects_have_same_field_values(obj, cluster_representative, all_fields_to_unify):
                # Entering a new cluster
                cluster_representative = obj
                occurrence_number = 0
            occurrence_number += 1
            if occurrence_number > 1:
                old_value = getattr(obj, self.field)
                new_value = self.unify_value(old_value, occurrence_number, obj)
                setattr(obj, self.field, new_value)
                obj.save()

    def _undo_field_unification(self, apps, schema_editor):
        """Undo field unification"""
        if not self.enable_revert:
            return
        for obj in self._get_iterator(self._get_model_queryset(apps, schema_editor)):
            old_value = getattr(obj, self.field)
            new_value = self.revert_unified_value(old_value, obj)
            if old_value != new_value:
                setattr(obj, self.field, new_value)
                obj.save()

    def __init__(
            self,
            app: str,
            model: str,
            field: str,
            with_respect_to: MultipleStrings,
            enable_revert: bool,
            unification_ordering: MultipleStrings = (),
            processing_chunk_size: int = None,
            *args, **kwargs):
        with_respect_to = convert_names_to_tuple(with_respect_to, "with_respect_to")
        unification_ordering = convert_names_to_tuple(unification_ordering, "unification_ordering")
        if processing_chunk_size is None:
            processing_chunk_size = 100
        self.app = app
        self.model = model
        self.field = field
        self.with_respect_to_fields = with_respect_to
        self.enable_revert = enable_revert
        self.unification_ordering = unification_ordering
        self.processing_chunk_size = processing_chunk_size
        super().__init__(
            code=self._unify_field,
            reverse_code=self._undo_field_unification,
            *args, **kwargs
        )

    def field_description(self):
        return f"'{self.field}' on {self.app}.{self.model}"

    def with_respect_to_description(self):
        return f"with respect to {self.with_respect_to_fields}" if self.with_respect_to_fields else ""


class UnifyStringField(AbstractStringUnificationOperation):
    """
    Database migration operation to make a (unlimited or sufficiently long) string field have unique values.

    This operation is mainly used before adding a unique constraint on the corresponding field.

    Assume that the value 'hello' appears 3 times.
    It will become 'hello', 'hello__unified__2__', 'hello__unified__3__'

    If 'with_respect_to' is specified, then the 'field' is unified within that scope.
    In other words, (field, *with_respoect_to_fields) will form a unique key.

    When undoing the operation, the field is modified only when 'enable_revert' is True.
    'enable_revert' is True by default.
    """

    UNIFICATION_STR = "UNIFIED"
    NULL_UNIFICATION_STR = "UNIFIED_NULL"
    regex_pattern_for_unification = re.compile(r"(.*)__{}__(\d+)__".format(UNIFICATION_STR), re.DOTALL)
    regex_pattern_for_null_unification = re.compile(r"__{}__(\d+)__".format(NULL_UNIFICATION_STR))

    # Override
    def unify_value(self, value: str, occurrence_number: int, obj) -> str:
        if value is None:
            return f"__{self.NULL_UNIFICATION_STR}__{occurrence_number}__"
        return f"{value}__{self.UNIFICATION_STR}__{occurrence_number}__"

    # Override
    def revert_unified_value(self, value: str, obj) -> str:
        if value is None or self.regex_pattern_for_null_unification.fullmatch(value):
            return None
        m = self.regex_pattern_for_unification.fullmatch(value)
        return value if m is None else m.group(1)


    def __init__(
            self,
            app: str,
            model: str,
            field: str,
            with_respect_to: MultipleStrings = (),
            enable_revert: bool = True,
            unification_ordering: MultipleStrings = (),
            processing_chunk_size: int = None,
            *args, **kwargs):
        super().__init__(
            app=app,
            model=model,
            field=field,
            with_respect_to=with_respect_to,
            enable_revert=enable_revert,
            unification_ordering=unification_ordering,
            processing_chunk_size=processing_chunk_size,
            *args, **kwargs
        )

    # Override
    def describe(self):
        return f"Unify field {self.field_description()} {self.with_respect_to_description()}"


class UnifyShortStringField(AbstractStringUnificationOperation):
    """
    Database migration operation to make a short string field have unique values.

    This operation is mainly used before adding a unique constraint on the corresponding field.

    Assume that the value 'hello' appears 3 times and {pk} is 3 digits.
    The first appearance remains 'hello'.
    The next appearances depend on the value of 'max_length' (the limit on the string field):
    * max_length=8: 'hello_{pk}'
    * max_length=7: 'hell_{pk}'
    * max_length=4: '_{pk}'
    * max_length=3: '{pk}'
    * max_length=2: two right-most digits of '{pk}'
    * max_length=1: right-most digit of '{pk}'

    If 'with_respect_to' is specified, then the 'field' is unified within that scope.
    In other words, (field, *with_respoect_to_fields) will form a unique key.

    When undoing the operation, the field is modified only when 'enable_revert' is True.
    Note that revrting the unification may not work properly.
    'enable_revert' is False by default.
    """

    # Override
    def unify_value(self, value: str, occurrence_number: int, obj) -> str:
        if value is None:
            return f"__N{obj.pk}"[-self.max_length:]
        suffix = f"_{obj.pk}"
        if self.max_length <= len(suffix):
            # We can keep only (a part of) the suffix
            return suffix[-self.max_length:]
        truncated_value = value[:self.max_length-len(suffix)]
        return truncated_value+suffix

    # Override
    def revert_unified_value(self, value: str, obj) -> str:
        if value is None or value == f"__N{obj.pk}":
            return None
        suffix = f"_{obj.pk}"
        if self.max_length <= len(suffix):
            # The main data of the value is replaced by suffix and lost.
            return value
        if not value.endswith(suffix):
            # Unmodified or shortened when value was None
            return value
        return value[:-len(suffix)] #truncated_value

    def __init__(
            self,
            app: str,
            model: str,
            field: str,
            max_length: int,
            with_respect_to: MultipleStrings = (),
            enable_revert: bool = False,
            unification_ordering: MultipleStrings = (),
            processing_chunk_size: int = None,
            *args, **kwargs):
        self.max_length = max_length
        super().__init__(
            app=app,
            model=model,
            field=field,
            with_respect_to=with_respect_to,
            enable_revert=enable_revert,
            unification_ordering=unification_ordering,
            processing_chunk_size=processing_chunk_size,
            *args, **kwargs
        )

    # Override
    def describe(self):
        return f"Unify short string field {self.field_description()} {self.with_respect_to_description()}"


class UpdateContentType(migrations.RunPython):
    """Database migration operation to update a ContentType"""

    def _update_contenttype_func(self, old_app: str, old_model: str, new_app: str, new_model: str):
        def func(apps, schema_editor):
            ContentType.objects \
                .filter(app_label=old_app, model=old_model) \
                .update(app_label=new_app, model=new_model)
            ContentType.objects.clear_cache()
        return func

    def __init__(self, app: str, model: str, new_app: str = None, new_model: str = None):
        if new_app is None:
            new_app = app
        if new_model is None:
            new_model = model
        self.app = app
        self.model = model
        self.new_app = new_app
        self.new_model = new_model
        super().__init__(
            code=self._update_contenttype_func(
                old_app=app, old_model=model, new_app=new_app, new_model=new_model
            ),
            reverse_code=self._update_contenttype_func(
                old_app=new_app, old_model=new_model, new_app=app, new_model=model
            ),
        )

    def describe(self):
        return (f"Update ContentType {self.app}.{self.model}"
                f" to {self.new_app}.{self.new_model}")


def qn(name: str) -> str:
    """quote_name function for quoting names in sql commands"""
    return connection.ops.quote_name(name)


class RenameSequence(migrations.RunSQL):
    """Database migration operation to rename a sequence"""

    def _rename_sequence_sql(self, old_name: str, new_name: str) -> str:
        return f"ALTER SEQUENCE {qn(old_name)} RENAME TO {qn(new_name)}"

    def __init__(self, name: str, new_name: str):
        self.name = name
        self.new_name = new_name
        super().__init__(
            sql=self._rename_sequence_sql(old_name=name, new_name=new_name),
            reverse_sql=self._rename_sequence_sql(old_name=new_name, new_name=name),
        )

    def describe(self):
        return f"Rename sequence {self.name} to {self.new_name}"


class RenameTableIdSequence(RenameSequence):
    """Database migration operation to rename the ID sequence of a table"""

    DEFAULT_TABLE_ID_COLUMN_NAME: str = 'id'

    def _table_column_sequence_name(self, table: str, column: str) -> str:
        return f"{table}_{column}_seq"

    def __init__(
            self,
            table: str,
            new_table: str,
            id_column: str = None,
            new_id_column: str = None,
        ):
        if id_column is None:
            id_column = self.DEFAULT_TABLE_ID_COLUMN_NAME
        if new_id_column is None:
            new_id_column = id_column
        self.table = table
        self.new_table = new_table
        self.id_column = id_column
        self.new_id_column = new_id_column
        super().__init__(
            name=self._table_column_sequence_name(table=table, column=id_column),
            new_name=self._table_column_sequence_name(table=new_table, column=new_id_column),
        )

    def describe(self):
        return (f"Rename table-id sequence for {self.table}.{self.id_column}"
                f" to {self.new_table}.{self.new_id_column}")


class RenameIndex(migrations.RunSQL):
    """Database migration operation to rename an index"""

    def _rename_index_sql(self, old_name: str, new_name: str) -> str:
        return f"ALTER INDEX {qn(old_name)} RENAME TO {qn(new_name)}"

    def __init__(self, name: str, new_name: str):
        self.name = name
        self.new_name = new_name
        super().__init__(
            sql=self._rename_index_sql(old_name=name, new_name=new_name),
            reverse_sql=self._rename_index_sql(old_name=new_name, new_name=name),
        )

    def describe(self):
        return f"Rename index {self.name} to {self.new_name}"


class RenameTableColumnsIndex(RenameIndex):
    """Database migration operation to rename an index based on table-columns"""

    def _index_name(self, table: str, columns: StringTuple, suffix: str):
        with connection.schema_editor() as schema_editor:
            return schema_editor._create_index_name(
                table_name=table,
                column_names=columns,
                suffix=suffix,
            )

    def __init__(self,
            table: str,
            columns: MultipleStrings,
            new_table: str = None,
            new_columns: MultipleStrings = None,
            suffix: str = '',
            new_suffix: str = None,
        ):
        columns = convert_names_to_tuple(columns, "columns")
        if new_table is None:
            new_table = table
        if new_columns is None:
            new_columns = columns
        else:
            new_columns = convert_names_to_tuple(new_columns, "new_columns")
        if new_suffix is None:
            new_suffix = suffix
        self.table = table
        self.columns = columns
        self.new_table = new_table
        self.new_columns = new_columns
        self.suffix = suffix
        self.new_suffix = new_suffix
        super().__init__(
            name=self._index_name(table=table, columns=columns, suffix=suffix),
            new_name=self._index_name(table=new_table, columns=new_columns, suffix=new_suffix),
        )

    def describe(self):
        return (f"Rename table-columns index for {self.table}{self.columns}{self.suffix}"
                f" to {self.new_table}{self.new_columns}{self.new_suffix}")


class RenameTableConstraint(migrations.RunSQL):
    """Database migration operation to rename a table constraint"""

    def _rename_constraint_sql(self, table: str, old_constraint_name: str, new_constraint_name: str) -> str:
        return f"ALTER TABLE {qn(table)} RENAME CONSTRAINT {qn(old_constraint_name)} TO {qn(new_constraint_name)}"

    def __init__(self, table: str, constraint_name: str, new_constraint_name: str):
        self.table = table
        self.constraint_name = constraint_name
        self.new_constraint_name = new_constraint_name
        super().__init__(
            sql=self._rename_constraint_sql(
                table=table, old_constraint_name=constraint_name, new_constraint_name=new_constraint_name
            ),
            reverse_sql=self._rename_constraint_sql(
                table=table, old_constraint_name=new_constraint_name, new_constraint_name=constraint_name
            ),
        )

    def describe(self):
        return f"Rename constraint {self.constraint_name} to {self.new_constraint_name} in table {self.table}"


class RenameTablePrimaryKeyConstraint(RenameTableConstraint):
    """
    Database migration operation to rename the primary key constraint of a table

    This operation assumes the table itself is already renamed in previous operations.
    So, it applies the rename operation on the new table name.
    """

    def _pk_constraint_name(self, table: str) -> str:
        return f"{table}_pkey"

    def __init__(self, table: str, new_table: str):
        self.old_table = table
        self.new_table = new_table
        super().__init__(
            table=new_table,
            constraint_name=self._pk_constraint_name(table=table),
            new_constraint_name=self._pk_constraint_name(table=new_table),
        )

    def describe(self):
        return (f"Rename the primary key constraint of table {self.old_table}"
                f" to table {self.new_table}")


class RenameTableForeignKeyConstraint(RenameTableConstraint):
    """
    Database migration operation to rename the foreign key constraint of a table

    This operation assumes the table itself is already renamed in previous operations.
    So, it applies the rename operation on the new table name.
    """

    def _fk_constraint_name(
            self,
            table: str,
            columns: StringTuple,
            target_table: str,
            target_columns: StringTuple,
        ) -> str:
        with connection.schema_editor() as schema_editor:
            return schema_editor._create_index_name(
                table_name=table,
                column_names=columns,
                suffix=f"_fk_{target_table}_{target_columns[0]}"
            )

    DEFAULT_TABLE_ID_COLUMN_NAME: str = 'id'

    def __init__(
            self,
            table: str,
            columns: MultipleStrings,
            target_table: str,
            target_columns: MultipleStrings = None,
            new_table: str = None,
            new_columns: MultipleStrings = None,
            new_target_table: str = None,
            new_target_columns: MultipleStrings = None,
        ):
        columns = convert_names_to_tuple(columns, "columns")
        if target_columns is None:
            target_columns = self.DEFAULT_TABLE_ID_COLUMN_NAME
        target_columns = convert_names_to_tuple(target_columns, "target_columns")
        if new_table is None:
            new_table = table
        if new_columns is None:
            new_columns = columns
        else:
            new_columns = convert_names_to_tuple(new_columns, "new_columns")
        if new_target_table is None:
            new_target_table = target_table
        if new_target_columns is None:
            new_target_columns = target_columns
        else:
            new_target_columns = convert_names_to_tuple(new_target_columns, "new_target_columns")
        self.table = table
        self.columns = columns
        self.target_table = target_table
        self.target_columns = target_columns
        self.new_table = new_table
        self.new_columns = new_columns
        self.new_target_table = new_target_table
        self.new_target_columns = new_target_columns
        super().__init__(
            table=new_table,
            constraint_name=self._fk_constraint_name(
                table=table, columns=columns, target_table=target_table, target_columns=target_columns,
            ),
            new_constraint_name=self._fk_constraint_name(
                table=new_table, columns=new_columns, target_table=new_target_table, target_columns=new_target_columns,
            ),
        )

    def describe(self):
        return (f"Rename the foreign key constraint for {self.table}{self.columns}->{self.target_table}{self.target_columns}"
                f" to {self.new_table}{self.new_columns}->{self.new_target_table}{self.new_target_columns}")
