import 'dart:convert';

import 'package:api_client/api_client.dart';
import 'package:logger/logger.dart';

/// {@template recommendation_resource}
/// A client to communicate with the recommendation endpoints.
/// {@endtemplate}
class RecommendationResource {
  /// {@macro recommendation_resource}
  RecommendationResource({
    required HttpApiClient client,
  }) : _client = client;

  final HttpApiClient _client;
  final _logger = Logger();
  static const String _basePath = '/recommenders';

  /// Fetches collaborative filtering recommendations for a student.
  Future<String> fetchPMRecommendations({
    required int studentId,
    required String degreeId,
  }) async {
    try {
      final body = jsonEncode({
        'student_id': studentId,
        'degree_id': degreeId,
        'algorithm': 'pm',
      });
      final response = await _client.post(
        '$_basePath/predict',
        body: body,
      );
      return response.body;
    } catch (e) {
      _logger.e(
        'Error fetching random forest '
        'recommendations for studentId: $studentId',
        error: e,
      );
      rethrow;
    }
  }

  /// Fetches rule-based recommendations for a student and course.
  Future<String> fetchDTRecommendations({
    required String course,
    required String degreeId,
  }) async {
    try {
      final body = jsonEncode({
        'analysis_config': {
          'combinations': ['behav'],
          'feature': 'Course-Order',
          'is_binary_label': true,
          'is_atomic': true,
          'label_index': 1,
          'max_depth': 5,
          'course': course,
          'label': 'string',
          'index_type': 'string',
          'is_pm': true,
        },
        'include_raw_data': true,
        'sample_size': 0,
        'degree_id': degreeId,
        'output_to_s3': true,
        'include_data_summary': true,
      });

      final response = await _client.post(
        '$_basePath/asb',
        body: body,
      );

      return response.body;
    } catch (e) {
      _logger.e(
        'Error fetching rule-based recommendations '
        'for course: $course, degreeId: $degreeId',
        error: e,
      );
      rethrow;
    }
  }

  /// Fetches success probability recommendations for candidate subjects.
  Future<String> fetchCSRecommendations({
    required int studentId,
    required List<String> candidateSubjects,
    required String degreeId,
  }) async {
    try {
      final body = jsonEncode({
        'algorithm': 'rf',
        'degree_id': degreeId,
        'student_id': studentId,
        'candidate_subjects': candidateSubjects,
      });

      final response = await _client.post(
        '$_basePath/predict',
        body: body,
      );
      return response.body;
    } catch (e) {
      _logger.e(
        'Error fetching success probability '
        ' recommendations for studentId: $studentId',
        error: e,
      );
      rethrow;
    }
  }
}
