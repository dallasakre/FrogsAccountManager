angular
    .module('app')
    .controller('DatabaseCtrl', DatabaseCtrl);

DatabaseCtrl.$inject = ['$scope','$http','$cookies'];

function DatabaseCtrl($scope, $http, $cookies) {

    var vm = this;
    vm.loadDatabases = loadDatabases;
    vm.maxLength = 2048;
    vm.today = new Date();
    var selectedDbs = [];

    function loadDatabases() {
        var objFrogsDb = $cookies.getObject('frogsdbs')
        if (objFrogsDb == null || objFrogsDb == undefined) {
            $http.get('/api/v1/get-frogs-database')
                .then(function (response) {
                    $cookies.putObject('frogsdbs', response.data.frogs_databases);
                    objFrogsDb = response.data.frogs_databases;
                    vm.databases = objFrogsDb;
                });
        } else {
            vm.databases = objFrogsDb;
        }
    };

    $scope.checkAll = function() {
        if (!$scope.selectedAll) {
            $scope.selectedAll = true;
        } else {
            $scope.selectedAll = false;
        }
        angular.forEach(vm.databases, function (row) {
            row.Selected = $scope.selectedAll;
        });
    };

//    $scope.isAllChecked = function () {
//        $scope.selectedAll = vm.databases.every(function (row) {
//            return row.Selected;
//        }) 
    //    }

    $scope.getSelectedDbs = function () {
        angular.forEach(vm.databases, function (row) {
            if (row.Selected) {
                selectedDbs.push(row.database);
            }
        });
        return selectedDbs;
    }

    $scope.getSelectedRdo = function () {
        value = $scope.rdoValue;
        console.log(value);
        return value;
    }

};

