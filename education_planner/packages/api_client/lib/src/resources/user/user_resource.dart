import 'dart:convert';

import 'package:api_client/api_client.dart';

/// {@template user_resource}
/// A client for the user resource.
/// {@endtemplate}
class UserResource {
  /// {@macro user_resource}
  UserResource({required HttpApiClient client}) : _client = client;

  final HttpApiClient _client;

  /// The API endpoint for user sign-up.
  static const signUpPath = 'students/signup';

  /// The API endpoint for user log-in.
  static const loginPath = 'students/login';

  /// Performs a log-in operation with the provided information.
  /// Throws an exception if an error occurs.
  Future<void> login({
    required String username,
    required String password,
  }) async {
    try {
      await _client.post(
        loginPath,
        body: {
          'username': username,
          'password': password,
        },
      );
    } on Exception {
      rethrow;
    }
  }

  /// Attempts to sign up a new user with the provided [request].
  /// Throws a [SignUpFailure] if an error occurs.
  Future<void> signUp(SignUpRequest request) async {
    try {
      final response = await _client.post(
        signUpPath,
        body: request.toJson(),
      );
      if (response.statusCode == 201) {
        return;
      } else if (response.statusCode == 409) {
        throw EmailAlreadyExistFailure(
          'Failed to sign up user: ${response.statusCode} ${response.body}',
          StackTrace.current,
        );
      } else {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        final message = body['message'] as String;
        throw SignUpFailure(
          'Failed to sign up user: $message [${response.statusCode}]',
          StackTrace.current,
        );
      }
    } on Exception {
      rethrow;
    }
  }
}
