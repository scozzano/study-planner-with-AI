import 'package:form_inputs/form_inputs.dart';
import 'package:test/test.dart';

void main() {
  const emailString = 'test@gmail.com';
  group('Email', () {
    group('constructors', () {
      test('pure creates correct instance', () {
        const email = Email.pure();
        expect(email.value, '');
        expect(email.isPure, true);
      });

      test('dirty creates correct instance', () {
        const email = Email.dirty(emailString);
        expect(email.value, emailString);
        expect(email.isPure, false);
      });
    });

    group('validator', () {
      test('returns empty error when email is empty', () {
        expect(
          const Email.dirty().error,
          EmailValidationError.empty,
        );
      });

      test('returns invalid error when email is malformed', () {
        expect(
          const Email.dirty('test').error,
          EmailValidationError.invalid,
        );
      });

      test('is valid when email is valid', () {
        expect(
          const Email.dirty(emailString).error,
          isNull,
        );
      });

      test('equality should work correctly', () {
        const email1 = Email.dirty('test1@email.com');
        const email2 = Email.dirty('test1@email.com');
        const email3 = Email.dirty('test2@email.com');

        expect(
          email1,
          equals(email2),
        );
        expect(
          email1 == email3,
          isFalse,
        );
      });
    });
  });
}
