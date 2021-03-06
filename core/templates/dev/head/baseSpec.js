// Copyright 2014 The Oppia Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Unit tests for the base controller.
 *
 * @author sll@google.com (Sean Lip)
 */

describe('Base controller', function() {

  describe('BaseCtrl', function() {
    var scope, ctrl, $httpBackend;

    beforeEach(inject(function($rootScope, $controller) {
      scope = $rootScope.$new();
      ctrl = $controller(Base, {
        $scope: scope, warningsData: null, activeInputData: null,
        messengerService: null});
    }));

    it('should clone an object', function() {
      var a = {'a': 'b'};
      var b = scope.cloneObject(a);
      expect(b).toEqual(a);
      expect(b).not.toBe(a);
      a['b'] = 'c';
      expect(b).not.toEqual(a);
    });

    it('should correctly normalize whitespace', function(warningsData) {
      expect(scope.normalizeWhitespace('a')).toBe('a');
      expect(scope.normalizeWhitespace('a  ')).toBe('a');
      expect(scope.normalizeWhitespace('  a')).toBe('a');
      expect(scope.normalizeWhitespace('  a  ')).toBe('a');

      expect(scope.normalizeWhitespace('a  b ')).toBe('a b');
      expect(scope.normalizeWhitespace('  a  b ')).toBe('a b');
      expect(scope.normalizeWhitespace('  ab c ')).toBe('ab c');
    });

    it('should correctly validate entity names', function(warningsData) {
      GLOBALS = {INVALID_NAME_CHARS: 'ace'};

      expect(scope.isValidEntityName('b')).toBe(true);
      expect(scope.isValidEntityName('b   ')).toBe(true);
      expect(scope.isValidEntityName('   b')).toBe(true);
      expect(scope.isValidEntityName('bd')).toBe(true);

      expect(scope.isValidEntityName('')).toBe(false);
      expect(scope.isValidEntityName('   ')).toBe(false);
      expect(scope.isValidEntityName('a')).toBe(false);
      expect(scope.isValidEntityName('c')).toBe(false);
      expect(scope.isValidEntityName('ba')).toBe(false);
    });
  });
});
