angular
    .module('app')
    .controller('AccountCtrl', AccountCtrl);

AccountCtrl.$inject = ['$scope', '$http'];

function AccountCtrl($scope, $http) {

    var vm = this;
    vm.parameter;
    vm.loadAccounts = loadAccounts;

    function loadAccounts() {
        $http.get('/api/v1/get-all-frogs-accounts/' + vm.parameter)
            .then(function (response) {
                vm.accounts = response.data.frogs_users;
            });
    };
};