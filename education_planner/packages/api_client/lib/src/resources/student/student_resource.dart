import 'dart:async';
import 'dart:convert';

import 'package:api_client/api_client.dart';
import 'package:http/http.dart';
import 'package:logger/logger.dart';

/// {@template schooling_not_found_exception}
/// Exception thrown when schooling is not found for a student.
/// {@endtemplate}
class SchoolingNotFoundException implements Exception {
  /// {@macro schooling_not_found_exception}
  SchoolingNotFoundException([this.message = 'Schooling not found.']);

  /// The message of the exception
  final String message;

  @override
  String toString() => 'SchoolingNotFoundException: $message';
}

/// {@template student_resource}
/// A client to communicate with the student resource.
/// {@endtemplate}
class StudentResource {
  /// {@macro student_resource}
  StudentResource({
    required HttpApiClient client,
  }) : _client = client;

  final HttpApiClient _client;
  final _logger = Logger();
  static const String _studentsPath = '/students';
  static const String _studentsSchoolingResource = '$_studentsPath/schooling';
  String _studentsSchoolingIdResource(String studentId, String degreeId) {
    return '$_studentsPath/$studentId/$degreeId/schooling';
  }

  /// Submits the schooling [pdf] in a base64 encoded string.
  FutureOr<void> submitSchoolingPdf({
    required String pdf,
  }) async {
    try {
      final jsonBody = {
        'file': pdf,
      };
      await _client.post(
        _studentsSchoolingResource,
        body: jsonEncode(jsonBody),
        options: const ApiRequestOptions(
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        ),
      );
    } on Exception catch (e) {
      _logger.e('Error submitting schooling PDF', error: e);
    }
  }

  /// Fetches the student schooling
  /// information.
  FutureOr<String> fetchSchooling({
    required String studentId,
    required String degreeId,
  }) async {
    try {
      final response = await _client.get(
        _studentsSchoolingIdResource(studentId, degreeId),
      );
      if (response.statusCode == 404) {
        throw SchoolingNotFoundException(
          'Schooling not found for student ID: $studentId',
        );
      }
      return response.body;
    } on ClientException {
      throw SchoolingNotFoundException(
        'Schooling not found for student ID: $studentId',
      );
    } on Exception {
      throw SchoolingNotFoundException(
        'Schooling not found for student ID: $studentId',
      );
    }
  }
}
