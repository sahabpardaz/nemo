# Nemo: Frontend

This is the UI of Nemo and it was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Structure
```
│
└───public : Static files
│   │   AppConfig.js : Some general configurations such as API url, etc
│   │   ...
│   
└───src : Logics implemented in javascript language
    |   index.js : Rendering starts here
    │   apiURLs.js : All required API endpoint URLs that are needed at the frontend
    │   ...
    |
    └───components : Inner reusable components that are used in one or many pages
    |   │   ...
    |
    └───pages : Web pages that may consist of some other components.
        │   ...
```

## How to run

1. Edit `API_URL` in `AppConfig.js` first

2. Downloads dependencies
```
npm install
```
3. Runs the app in the development mode.  
```
npm start
```
