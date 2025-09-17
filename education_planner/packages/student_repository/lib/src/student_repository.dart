import 'dart:convert';

import 'package:api_client/api_client.dart';
import 'package:student_repository/student_repository.dart';

/// {@template student_repository}
/// A repository to handle student related operations.
/// {@endtemplate}
class StudentRepository {
  /// {@macro student_repository}
  const StudentRepository({
    required ApiClient client,
  }) : _client = client;

  final ApiClient _client;

  /// Submits the schooling [pdf] in a base64 encoded string.
  Future<void> submitSchoolingPdf({
    required String pdf,
  }) async {
    await _client.studentResource.submitSchoolingPdf(
      pdf: pdf,
    );
  }

  /// Fetches the student schooling
  /// information.
  Future<Schooling> fetchSchooling({
    required String studentId,
    required String degreeId,
  }) async {
    try {
      final response = await _client.studentResource.fetchSchooling(
        studentId: studentId,
        degreeId: degreeId,
      );
      final json = jsonDecode(response) as Map<String, dynamic>;
      final schooling = Schooling.fromJson(json);
      return schooling;
    } catch (e) {
      rethrow;
    }
  }
}
