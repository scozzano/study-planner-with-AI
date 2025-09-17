import 'package:api_client/api_client.dart';
import 'package:auth_client/auth_client.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:user_repository/user_repository.dart';

class MockApiClient extends Mock implements ApiClient {}

class MockAuthenticationClient extends Mock implements AuthenticationClient {}

class MockUserResource extends Mock implements UserResource {}

void main() {
  group('UserRepository', () {
    late ApiClient apiClient;
    late AuthenticationClient authenticationClient;
    late UserResource userResource;
    late UserRepository repository;

    const validEmail = 'example@mail.com';
    const validPassword = 'password';
    const validName = 'Name';
    const validUser = AuthenticationUser(id: 'id', email: 'email');

    setUp(() {
      apiClient = MockApiClient();
      authenticationClient = MockAuthenticationClient();
      userResource = MockUserResource();
      repository = UserRepository(
        apiClient: apiClient,
        authenticationClient: authenticationClient,
      );
    });

    test('can be instantiated', () {
      expect(
        UserRepository(
          apiClient: apiClient,
          authenticationClient: authenticationClient,
        ),
        isNotNull,
      );
    });

    test('can be instantiated', () {
      expect(
        UserRepository(
          apiClient: apiClient,
          authenticationClient: authenticationClient,
        ),
        isNotNull,
      );
    });

    group('Authentication status changed', () {
      test('authentication event with session expired state', () async {
        const authenticationEvent =
            AuthenticationEvent(type: AuthEventType.sessionExpired);
        final user = await repository.onAuthStatusChanged(authenticationEvent);

        expect(user, null);
      });

      test('authentication event with signed out state', () async {
        const authenticationEvent =
            AuthenticationEvent(type: AuthEventType.signedOut);
        final user = await repository.onAuthStatusChanged(authenticationEvent);

        expect(user, null);
      });

      test('authentication event with user deleted state', () async {
        const authenticationEvent =
            AuthenticationEvent(type: AuthEventType.userDeleted);
        final user = await repository.onAuthStatusChanged(authenticationEvent);

        expect(user, null);
      });

      test('authentication event with signed in state', () async {
        const authenticationEvent =
            AuthenticationEvent(type: AuthEventType.signedIn, user: validUser);
        final user = await repository.onAuthStatusChanged(authenticationEvent);

        expect(user, isA<User>());
      });

      test('calls auth status change on AuthenticationClient', () {
        when(() => authenticationClient.onAuthStatusChanged).thenAnswer(
          (_) => const Stream.empty(),
        );
        repository.user;
        verify(() => authenticationClient.onAuthStatusChanged).called(1);
      });
    });

    group('Sign up', () {
      test('signs up user success', () {
        when(() => apiClient.userResource).thenReturn(userResource);
        when(
          () => userResource.signUp(
            const SignUpRequest(
              email: validEmail,
              password: validPassword,
              name: validName,
            ),
          ),
        ).thenAnswer((_) async {});

        expect(
          () async => repository.signUp(
            email: validEmail,
            password: validPassword,
            name: validName,
          ),
          returnsNormally,
        );
      });

      test('signs up user failure', () {
        when(() => apiClient.userResource.signUp(any())).thenThrow(Exception());

        expect(
          () async => repository.signUp(
            email: validEmail,
            password: validPassword,
            name: validName,
          ),
          throwsA(isA<Exception>()),
        );
      });

      test('signs up user with empty mail', () {
        expect(
          () async => repository.signUp(
            email: '',
            password: validPassword,
            name: validName,
          ),
          throwsA(isA<AssertionError>()),
        );
      });

      test('signs up user with empty password', () {
        expect(
          () async => repository.signUp(
            email: validEmail,
            password: '',
            name: validName,
          ),
          throwsA(isA<AssertionError>()),
        );
      });

      test('signs up user with empty name', () async {
        expect(
          () async => repository.signUp(
            email: validEmail,
            password: validPassword,
            name: '',
          ),
          throwsA(isA<AssertionError>()),
        );
      });
    });

    group('Sign in', () {
      test('sign in success', () async {
        when(
          () => authenticationClient.signInUser(
            email: validEmail,
            password: validPassword,
          ),
        ).thenAnswer((_) async {});

        expect(
          () async => repository.signIn(
            email: validEmail,
            password: validPassword,
          ),
          returnsNormally,
        );
      });

      test('sign in failure', () async {
        when(
          () => authenticationClient.signInUser(
            email: validEmail,
            password: validPassword,
          ),
        ).thenThrow(Exception());

        expect(
          () async => repository.signIn(
            email: validEmail,
            password: validPassword,
          ),
          throwsA(isA<SignInFailure>()),
        );
      });

      test('sign in with invalid user failure', () async {
        when(
          () => authenticationClient.signInUser(
            email: validEmail,
            password: validPassword,
          ),
        ).thenThrow(
          InvalidUserFailure(Exception(), StackTrace.empty),
        );

        expect(
          () async => repository.signIn(
            email: validEmail,
            password: validPassword,
          ),
          throwsA(isA<InvalidUserFailure>()),
        );
      });

      test('sign in with empty mail', () async {
        expect(
          () async => repository.signIn(
            email: '',
            password: validPassword,
          ),
          throwsA(isA<AssertionError>()),
        );
      });

      test('verify mail with empty password', () async {
        expect(
          () async => repository.signIn(
            email: validEmail,
            password: '',
          ),
          throwsA(isA<AssertionError>()),
        );
      });
    });

    group('Sign out', () {
      test('sign out user succesfully', () {
        when(() => authenticationClient.signOut()).thenAnswer((_) async {});

        expect(
          () async => repository.signOut(),
          returnsNormally,
        );
      });

      test('sign out user unsuccesfully', () {
        when(() => authenticationClient.signOut()).thenThrow(Exception());

        expect(
          () async => repository.signOut(),
          throwsA(isA<SignOutFailure>()),
        );
      });
    });

    group('ReAuthenticate', () {
      test('reAuthenticate succesfully', () {
        when(
          () => authenticationClient.reAuthenticate(
            email: validEmail,
            password: validEmail,
          ),
        ).thenAnswer((_) async {});

        expect(
          () async => repository.reAuthenticate(
            email: validEmail,
            password: validEmail,
          ),
          returnsNormally,
        );
      });

      test('reauthenticate unsuccesfully', () {
        when(
          () => authenticationClient.reAuthenticate(
            email: validEmail,
            password: validEmail,
          ),
        ).thenThrow(Exception());

        expect(
          () async => repository.reAuthenticate(
            email: validEmail,
            password: validEmail,
          ),
          throwsA(isA<UserReAuthenticateFailure>()),
        );
      });
    });

    group('Delete account', () {
      test('deleted account succesfully', () {
        when(
          () => authenticationClient.deleteAccount(),
        ).thenAnswer((_) async {});

        expect(
          () async => repository.deleteAccount(),
          returnsNormally,
        );
      });

      test('deleted account unsuccesfully', () {
        when(
          () => authenticationClient.deleteAccount(),
        ).thenThrow(Exception());

        expect(
          () async => repository.deleteAccount(),
          throwsA(isA<UserDeleteAccountFailure>()),
        );
      });
    });
  });
}
