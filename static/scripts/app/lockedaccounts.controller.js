angular
    .module('app')
    .controller('DatabaseCtrl', DatabaseCtrl);

DatabaseCtrl.$inject = ['$scope','$http'];

function DatabaseCtrl($scope, $http) {

    var vm = this;
    vm.loadDatabases = loadDatabases;

    function loadDatabases() {
        $http.get('/api/v1/get-frogs-database')
            .then(function (response) {
                vm.databases = response.data.frogs_databases;
            });
    };
};