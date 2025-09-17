import 'dart:async';

import 'package:api_client/api_client.dart';
import 'package:auth_client/auth_client.dart';
import 'package:user_repository/user_repository.dart';

/// {@template user_repository}
/// A repository to handle all User related logic.
/// {@endtemplate}
class UserRepository {
  /// {@macro user_repository}
  UserRepository({
    required AuthenticationClient authenticationClient,
    required ApiClient apiClient,
  })  : _apiClient = apiClient,
        _authenticationClient = authenticationClient;

  final ApiClient _apiClient;
  final AuthenticationClient _authenticationClient;

  /// Maps the [AuthenticationEvent] to a [User] object.
  Future<User?> onAuthStatusChanged(AuthenticationEvent event) async {
    if (!event.type.isSignedIn) {
      return null;
    } else {
      final authUser = event.user;

      final user = User(
        id: authUser.id,
        email: authUser.email,
      );

      return user;
    }
  }

  /// Emits a new value when the authentication status changes.
  ///
  /// If the authentication status transitions from unauthenticated to
  /// authenticated, the [Stream] emits a valid [User] object.
  ///
  /// If the transition is from authenticated to unauthenticated, the [Stream]
  /// emits null.
  Stream<User?> get user {
    return _authenticationClient.onAuthStatusChanged.asyncMap(
      onAuthStatusChanged,
    );
  }

  /// Attempts to sign up the user with [email], [password] and [name].
  ///
  /// Throws a [SignUpFailure] if an exception occurs.
  Future<void> signUp({
    required String email,
    required String password,
    required String name,
  }) async {
    assert(
      email.isNotEmpty,
      () => throw ArgumentError('Email must not be empty'),
    );
    assert(
      password.isNotEmpty,
      () => throw ArgumentError('Password must not be empty'),
    );
    assert(
      name.isNotEmpty,
      () => throw ArgumentError('Name must not be empty'),
    );
    try {
      return _apiClient.userResource.signUp(
        SignUpRequest(
          email: email,
          password: password,
          name: name,
        ),
      );
    } on Exception {
      rethrow;
    }
  }

  /// Attempts to sign the user identified by [email] into the MessageDesk
  /// app by using the [password].
  ///
  /// Throws a [SignInFailure] if an exception occurs.
  Future<void> signIn({
    required String email,
    required String password,
  }) async {
    assert(
      email.isNotEmpty,
      () => throw ArgumentError('Email must not be empty'),
    );
    assert(
      password.isNotEmpty,
      () => throw ArgumentError('Password must not be empty'),
    );
    try {
      return _authenticationClient.signInUser(
        email: email,
        password: password,
      );
    } on InvalidUserFailure catch (error, stackTrace) {
      throw InvalidUserFailure(error, stackTrace);
    } on Exception catch (error, stackTrace) {
      throw SignInFailure(error, stackTrace);
    }
  }

  /// Signs out the current user.
  ///
  /// Throws a [SignOutFailure] if an exception occurs.
  Future<void> signOut() async {
    try {
      await _authenticationClient.signOut();
    } catch (error, stackTrace) {
      throw SignOutFailure(error, stackTrace);
    }
  }

  /// Deletes the current user
  ///
  /// Throws a [DeleteAccountFailure] if an exception occurs.
  Future<void> deleteAccount() async {
    try {
      await _authenticationClient.deleteAccount();
    } catch (error, stackTrace) {
      throw UserDeleteAccountFailure(error, stackTrace);
    }
  }

  /// Re-authenticates the current user
  ///
  /// Throws a [UserReAuthenticateFailure] if an exception occurs.
  Future<void> reAuthenticate({
    required String email,
    required String password,
  }) async {
    try {
      await _authenticationClient.reAuthenticate(
        email: email,
        password: password,
      );
    } catch (error, stackTrace) {
      throw UserReAuthenticateFailure(error, stackTrace);
    }
  }
}
