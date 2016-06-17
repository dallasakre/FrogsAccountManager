angular
    .module('app')
    .controller('AccountCtrl', AccountCtrl);

AccountCtrl.$inject = ['$scope','$http','$cookies','sweet','NgTableParams','$filter','ngTableDefaultGetData'];

function AccountCtrl($scope, $http, $cookies, sweet, NgTableParams, $filter, ngTableDefaultGetData) {

    var vm = this;
    vm.parameter;
    vm.loadDatabases = loadDatabases;
    vm.maxLength = 4000;
    vm.showtable = false;
    vm.showNoRecordsMsg = true;
    $scope.sortType = "'username'";
    $scope.sortReverse = false;
    $scope.searchAccounts = '';
    vm.allSelect = false;
    vm.dbChecked = false;
    vm.userIdsPassed = true;
    vm.btnSubmitDisabled = true;
    vm.btnValidateDisabled = true;
    $scope.currentPage = 1;
    $scope.pageSize = 20;

    vm.tableParams = new NgTableParams({},{records: vm.accounts});

    function loadDatabases() {
        var objFrogsDb = $cookies.getObject('frogsdb');
        var tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        if (objFrogsDb == null || objFrogsDb == undefined) {
            $http.get('/api/v1/get-frogs-database')
                .then(function (response) {
                    $cookies.putObject('frogsdb', response.data.frogs_databases, {expires: tomorrow});
                    objFrogsDb = response.data.frogs_databases;
                    vm.databases = objFrogsDb;
                });
        } else {
            vm.databases = objFrogsDb;
        }
    };


    $scope.enableSubmit = function() {
        vm.btnSubmitDisabled = true;
        if (vm.userIdsPassed && vm.dbChecked) {
            vm.btnSubmitDisabled = false;
        } else {
            vm.btnSubmitDisabled = true;
        }
    };

    $scope.checkAll = function() {
        vm.allSelect = $scope.selectedAll;
        angular.forEach(vm.databases, function (row) {
            row.Selected = vm.allSelect;
        });
        vm.dbChecked = vm.allSelect;
        $scope.enableSubmit();
    };


    $scope.anySelections = function () {
        vm.dbChecked = false;
        angular.forEach(vm.databases, function(row) {
            if (row.Selected) {
                vm.dbChecked = true;
            }
        $scope.enableSubmit();
        });
    };


    $scope.getSelectedDbs = function () {
        selectedDbs = [];
        angular.forEach(vm.databases, function (row) {
            if (row.Selected) {
                selectedDbs.push(row.database);
            }
        });
        console.log(selectedDbs);
        return selectedDbs;
    };

    $scope.filters = {
        username: '',
        region: '',
        database: '',
        dataset: '',
        role: ''
    }

    function loadAccounts(data) {
        $http.post("api/v1/post-all-frogs-accounts", data)
            .success(function (data, status, headers) {
                data = data.frogs_users;
                vm.showtable = true;
                vm.showNoRecordsMsg = false;
                vm.tableParams = new NgTableParams({
                    count: 20,
                    page: 1,
                    placeholder: '',
                    filter: $scope.filters,
                    sorting: {
                        username: 'asc',
                        region: 'asc',
                        dataset: 'asc',
                        role: 'asc'
                    },
                    group: {username: 'asc'}
                }, {dataset: data,
                    counts: [20,50,100],
                    groupBy: {role: 'asc'}
                });
            })
    };


    $scope.validateUsernames = function () {
        var pattern = /[$&+,:=?@#|'<>.\-^*()%!~%+{}\[\]/]/
        var qry = $scope.useridvals || "";
        if (qry.match(pattern)) {
            sweet.show('Oops!', 'Special character(s) were found.', 'error');
            vm.userIdsPassed = false;
            $scope.enableSubmit();
        } else {
            vm.userIdsPassed = true;
            $scope.enableSubmit();
        }
    };


    $scope.accountTable = function(){
        $scope['accountTable'] = {reload:function(){},settings:function(){return {}}};
        //$timeout(accountTable, 100)
    };


    $scope.exportData = function () {
        console.log($scope.filteredAccounts);

        var mystyle = {
            headers: true,
            column: {syle:{Font:{Bold:"1"}}}
        };
        alasql("SELECT * INTO XLSX('FROGS_User_Accounts.xlsx',?) FROM ?", [mystyle, ngTableDefaultGetData.filteredData]);
    };


    $scope.resetEverything = function () {
        sweet.show({
            title: "Are you sure?",
            text: "You are about to reset everything.",
            type: "warning",
            showCancelButton: true,
            confirmButtonColor: "#DD6B55",
            confirmButtonText: "Yes, reset it!",
            closeOnConfirm: false
        }, function (confirmed) {
            if (confirmed) {
                vm.loadDatabases();
                vm.accounts = null;
                vm.showtable = false;
                vm.showNoRecordsMsg = true;
                vm.tableParams.data = null;
                vm.btnSubmitDisabled = true;
                $scope.selectedAll = false;
                $scope.useridvals = "";
                $scope.$apply();
                sweet.show("Everything has been reset!");
            }
        }
        )};


    $scope.postSubmit = function () {
        var databases = $scope.getSelectedDbs();
        var users = []
        var data = {}
        vm.showNoRecordsMsg = true;
        if ($scope.useridvals != undefined && $scope.useridvals != "") {
            users = $scope.useridvals.replace(/ /g, "").split(";");
            data = {
                databases: databases,
                users: users
            }
            loadAccounts(data);
        } else {
            data = {
                databases: databases,
                users: users
            }
            sweet.show({
                title: "Are you sure you want ALL users from the selected databases?",
                text: "You did not list any specific users, so all users will be returned.",
                type: "warning",
                showCancelButton: true,
                showLoaderOnConfirm: true,
                confirmButtonColor: "#47a447",
                cancelButtonText: "No way Jose!",
                confirmButtonText: "Yep, let's do this!",
            }, function(confirmed) {
                if (confirmed) {
                    loadAccounts(data);
                }
            });
        };
    }


};