import 'package:form_inputs/form_inputs.dart';
import 'package:test/test.dart';

void main() {
  const passwordString = '12345678Aa!';
  group('Password', () {
    group('constructors', () {
      test('pure creates correct instance', () {
        const email = Password.pure();
        expect(email.value, '');
        expect(email.isPure, true);
      });

      test('dirty creates correct instance', () {
        const email = Password.dirty(passwordString);
        expect(email.value, passwordString);
        expect(email.isPure, false);
      });
    });

    group('validator', () {
      test('returns invalid error when password is empty', () {
        expect(
          const Password.dirty().error,
          PasswordValidationError.empty,
        );
      });

      test('returns invalid error when password is less than 6 characters', () {
        expect(
          const Password.dirty('test').error,
          PasswordValidationError.notLongEnough,
        );
      });

      test('is valid when password is valid', () {
        expect(
          const Password.dirty(passwordString).error,
          isNull,
        );
      });
    });
  });
}
