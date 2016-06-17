angular.module("ngTable").service(
    "$InterpolateUpdateService", function($templateCache, $interpolate){
        'use strict';

        this.changeGridInterpolate = function() {
            var templates = [
                'ng-table/filterRow.html',
                'ng-table/filters/number.html',
                'ng-table/filters/select-multiple.html',
                'ng-table/filters/select.html',
                'ng-table/filters/text.html',
                'ng-table/groupRow.html',
                'ng-table/header.html',
                'ng-table/pager.html',
                'ng-table/sorterRow.html'
            ];

            var start = $interpolate.startSymbol('{[');
            var end = $interpolate.endSymbol(']}');

            for (var i = 0; i < templates.length; i++) {
                var template = templates[i];
                var curTemplate = $templateCache.get(template);
                if (start !== "{{"){
                    curTemplate = curTemplate.replace(/\{\{/g, start);
                }
                if (end !== "}}"){
                    curTemplate = curTemplate.replace(/\}\}/g, end);
                }
                $templateCache.put(template, curTemplate);
            }
        };
    });

angular.module('ngTable').run(function($InterpolateUpdateService) {
    'use strict';

    $InterpolateUpdateService.changeGridInterpolate();
});