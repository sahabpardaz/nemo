# Nemo: Backend

It is the core of Nemo and provides Rest API for UI and submitting reports. It it developed with [Django](https://www.djangoproject.com/).

## Settings
General settings such as email cofiguration, celery connection, authentication methods, logging, ... are in `backend/` directory

## Apps
- ### Dashboard
    Provides rest API for provisioning the Maturity Model.

- ### DevOps Metrics
    Provides rest API to measure some DevOps metrics.
    Supported metrics:
    - Lead time
    - Time to restore
    - Deployment frequency
    - Change failure rate    

- ### ChangeList Reporter
    A toolkit that gets change lists from Gitlab and sends to DevOps metrics API.
    Supported source code managements:
    - Gitlab  

- ### Custom Scripts
    Scripts that can be used in special circumstances.
    - Remove deployments of changelists except latest ones
        ```
        python manage.py remove_deployments_of_changelists_except_latest_ones
        ```
    - Merge sequential evaluation reports into one if possible and remove the redudant ones.
        ```
        python manage.py remove_repeater_evaluation_reports
        ```

## Some Important Components
- ### Evaluators
    In order to automate the evaluation process of maturity model items, they are created to get run periodically. For each item type that could be automated, an evaluator should be created. Some evaluators are shown below.  
    - DevOpsMetricsEvaluators:
        - LeadTimeEvaluator
        - TimeToRestoreEvaluator
        - DeploymentFrequencyEvaluator
        - ChangeFailureRateEvaluator
    - CoverageEvaluators:
        - OverallTestCoverageEvaluator
        - IncrementalTestCoverageEvaluator
        - IsTestCoverageCalculatedEvaluator
    - DoryEvaluator: Evaluates based on Dory evaluations collected by `DoryEvaluationCollector` in data collectors.

    To create a new evaluator, you should create a new class inherited from the `Evaluator` class and implement your desired logic in the `evaluate` method.
- ### DataCollectors
    Some data from different providers need to be gathered and stored periodically, to help the automatic evaluations. This is done by `DataCollector`s.
    - OverallTestCoverageCollector : Collects overall coverage value from SonarQube
    - IncrementalTestCoverageCollector : Collects incremental coverage value from SonarQube
    - GerritChangeListCollector : Collects new changelists commited to main branch
    - DoryEvaluationCollector : Delegates the item evaluation to `Dory-Server` and saves the results. (What is [`Dory`](../../dory/)?)

## Database Models Diagram
Database models diagram can be generated with command:
```bash
python manage.py graph_models -a -o models.png
```
