angular
    .module('app')
    .controller('CreateUserCtrl', CreateUserCtrl);

CreateUserCtrl.$inject = ['$scope','$http','$cookies','sweet'];

function CreateUserCtrl($scope, $http, $cookies, sweet) {

    var vm = this;
    vm.loadDatabases = loadDatabases;
    vm.maxLength = 4000;
    //vm.minDate = new Date();
    $scope.rdoPerm = "READ_ONLY";
    $scope.rdoReadOnlyChecked = true;
    //$scope.chkExpire = true;
    //$scope.dtePickerDisabled = true;
    vm.btnSubmitDisabled = true;
    vm.btnValidateDisabled = true;


    function loadDatabases() {
        var objFrogsDb = $cookies.getObject('frogsdbs');
        var tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        if (objFrogsDb == null || objFrogsDb == undefined) {
            $http.get('/api/v1/get-frogs-database')
                .then(function (response) {
                    $cookies.putObject('frogsdbs', response.data.frogs_databases, {expires: tomorrow});
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

    //not implemented since Oracle expiration is done by profile, not user
    //$scope.toggleDatePicker = function () {
    //    if ($scope.rdoExpire) {
    //        $scope.dtePickerDisabled = true;
    //    } else {
    //        $scope.dtePickerDisabled = false;
    //    }
    //};

    $scope.enableValidate = function () {
        vm.btnSubmitDisabled = true;
        trimmedUserVals = $scope.useridvals.replace(/ /g, "");
        if (trimmedUserVals.length > 0) {
            vm.btnValidateDisabled = false;
        } else {
            vm.btnValidateDisabled = true;
        }
    };

    $scope.validateUsernames = function () {
        var pattern = /[$&+,:=?@#|'<>.\-^*()%!~%+{}\[\]/]/
        var qry = $scope.useridvals || "";
        console.log(qry.replace(/ /g, ""));
        if (qry.match(pattern)) {
            sweet.show('Oops!', 'Special character(s) were found.', 'error');
        } else {
            vm.btnSubmitDisabled = false;
            sweet.show('Good Job!', 'No special characters found.', 'success');
        }
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
                $scope.rdoReadOnlyChecked = true;
                //$scope.chkSExpire = true;
                $scope.useridvals = "";
                $scope.rdoPerm = 'READ_ONLY';
                $scope.$apply();
                sweet.show("Everything has been reset!");
            }
        }
        )};

    $scope.getSelectedDbs = function () {
        selectedDbs = []
        angular.forEach(vm.databases, function (row) {
            if (row.Selected) {
                selectedDbs.push(row.database + "-" + row.dataset);
            }
        });
        console.log(selectedDbs);
        return selectedDbs;
    };

    $scope.getSelectedRdo = function () {
        value = $scope.rdoPerm.toUpperCase();
        console.log(value);
        return value;
    };

    //not implemented since Oracle expiration is done by profile, not user
    //$scope.getExpiration = function () {
    //    if ($scope.rdoExpire || $scope.rdoExpire == undefined) {
    //        value = "never";
    //    } else {
    //        var d = new Date($scope.dteSelected);
    //        var year = d.getFullYear();
    //        var month = d.getMonth() + 1;
    //        if (month < 10) {
    //            month = "0" + month;
    //        }
    //        var day = d.getDate();
    //        value = year + "-" + month + "-" + day;
    //    }
    //    console.log(value);
    //    return value;
    //};

    $scope.postSubmit = function () {
        var database_dataset = $scope.getSelectedDbs();
        var permission = $scope.getSelectedRdo();
        var users = $scope.useridvals.replace(/ /g, "").split(";");

        if (database_dataset != undefined && database_dataset.length > 0) {

            var data = {
                database_dataset: database_dataset,
                permission: permission,
                //expiration: $scope.getExpiration(),
                users: users
            };

            sweet.show({
                title: "Are you sure you want to make these changes?",
                text: "You are about to Create/Modify the listed FROGS users.",
                type: "info",
                showCancelButton: true,
                closeOnConfirm: false,
                showLoaderOnConfirm: true,
                confirmButtonColor: "#47a447",
                cancelButtonText: "No way Jose!",
                confirmButtonText: "Yep, let's do this!",
            }, function(confirmed) {
                if (confirmed) {
                $http.post("api/v1/post-create-user", data)
                    .success(function (data, status, headers) {
                        var successcount = data.success_counter;
                        var failcount = data.failure_counter;
                        sweet.show("There were '" + successcount.toString() + "' Successes and '" + failcount.toString() + "' Failures.")
                    })
                    //.error(function (data, status, headers) {
                    }
                }
            );
        } else {
            sweet.show("Please select at least one Database/Dataset value!");
        }
    };

};

