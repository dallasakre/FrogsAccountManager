angular
    .module('app')
    .controller('LockedAccountsCtrl', LockedAccountsCtrl);

LockedAccountsCtrl.$inject = ['$scope','$http','$cookies','sweet'];

function LockedAccountsCtrl($scope, $http, $cookies, sweet) {

    var vm = this;
    vm.getLockedAccounts = getLockedAccounts;
    vm.showtable = false;
    vm.showNoLockedAccountsMsg = false;
    vm.allSelect = false;
    $scope.sortType = "'username'";
    $scope.sortReverse = false;
    $scope.searchAccounts = '';
    $scope.selectedAll = false;
    vm.btnSubmitDisabled = true;


    function getLockedAccounts() {
        $http.get('/api/v1/get-frogs-locked-accounts')
            .then(function (response) {
                if (response.data.frogs_locked_accounts.length > 0) {
                vm.showtable = true;
                $scope.selectedAll = false;
                vm.btnSubmitDisabled = true;
                vm.lockedaccounts = response.data.frogs_locked_accounts;
                }  else {
                vm.btnSubmitDisabled = true;
                vm.showtable = false;
                vm.showNoLockedAccountsMsg = true;
                }
            })
    };


    $scope.checkAll = function() {
        vm.allSelect = $scope.selectedAll;
        angular.forEach(vm.lockedaccounts, function (row) {
            row.Selected = vm.allSelect;
        });
    };


    $scope.getSelectedUsers = function () {
        selectedUsers = [];
        angular.forEach(vm.lockedaccounts, function (row) {
            if (row.Selected) {
                selectedUsers.push(row.username + ";" + row.database);
            }
        });
        console.log(selectedUsers);
        return selectedUsers;
    };


    $scope.anySelections = function () {
        vm.btnSubmitDisabled = true;
        angular.forEach(vm.lockedaccounts, function(row) {
            if (row.Selected) {
                vm.btnSubmitDisabled = false;
            }
        });
    };


    $scope.postSubmit = function () {
        var user_database = $scope.getSelectedUsers();

        if (user_database != undefined && user_database.length > 0) {
            records = [];
            data = [];

            for (i in user_database) {
                var account = user_database[i].split(";")[0];
                var database = user_database[i].split(";")[1];
                record = {
                    account: account,
                    database: database
                };
                records.push(record)
            }

            data = {
                frogs_locked_accounts: records
            };

            console.log(data);

            sweet.show({
                title: "Are you sure you want to unlock these users?",
                text: "You are about to Unlock the listed FROGS users.",
                type: "info",
                showCancelButton: true,
                closeOnConfirm: false,
                showLoaderOnConfirm: true,
                confirmButtonColor: "#47a447",
                cancelButtonText: "No way Jose!",
                confirmButtonText: "Yep, let's do this!",
            }, function(confirmed) {
                if (confirmed) {
                $http.post("api/v1/post-unlock-frogs-user", data)
                    .success(function (data, status, headers) {
                        var successcount = data.success_counter;
                        var failcount = data.failure_counter;
                        vm.getLockedAccounts();
                        // add logic to show different dialog if there are errors from PL/SQL
                        sweet.show({
                        title: "Process Completed!",
                        text: "Successful: '" + successcount.toString() + "', Failed: '" + failcount.toString() + "'.",
                        type: "info"
                        });
                     })
                }
            })
        } else {
            sweet.show("Please select at least one Database/Dataset value!");
        }
    };
};

