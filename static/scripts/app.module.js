var app = angular
    .module('app', ['ngCookies','hSweetAlert','angular-loading-bar','ngTable']);


app.config(['$interpolateProvider','cfpLoadingBarProvider', function ($interpolateProvider, cfpLoadingBarProvider) {
    $interpolateProvider.startSymbol('{[');
    $interpolateProvider.endSymbol(']}');
    cfpLoadingBarProvider.includeSpinner = false;
}]);