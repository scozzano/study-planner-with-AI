import 'dart:convert';

import 'package:api_client/api_client.dart';
import 'package:logger/logger.dart';
import 'package:planner_repository/planner_repository.dart';

/// {@template planner_repository}
/// A repository to handle the career planner data.
/// {@endtemplate}
class PlannerRepository {
  /// {@macro planner_repository}
  PlannerRepository({
    required ApiClient apiClient,
  }) : _apiClient = apiClient;

  final ApiClient _apiClient;
  final _logger = Logger();

  /// Fetches the university provided default data for
  /// a given career.
  Future<DegreePath> getDegreePath(String degreeId) async {
    try {
      final response = await _apiClient.pathResource
          .fetchDegreeRecommendedPath(degreeId: degreeId);

      final json = jsonDecode(response) as Map<String, dynamic>;
      final recommendedPath = DegreePath.fromJson(json);
      return recommendedPath;
    } catch (e) {
      _logger.e('Error fetching degree path for degreeId: $degreeId', error: e);
      rethrow;
    }
  }

  /// Fetches collaborative filtering recommendations for a student.
  Future<PMRecommendationResponse> getPMRecommendations({
    required int studentId,
    required String degreeId,
  }) async {
    try {
      final response =
          await _apiClient.recommendationResource.fetchPMRecommendations(
        studentId: studentId,
        degreeId: degreeId,
      );

      final json = jsonDecode(response) as Map<String, dynamic>;
      final recommendations = PMRecommendationResponse.fromJson(json);

      return recommendations;
    } catch (e) {
      _logger.e(
        'Error fetching collaborative filtering recommendations '
        'for studentId: $studentId',
        error: e,
      );
      rethrow;
    }
  }

  /// Fetches rule-based recommendations for a student and course.
  Future<List<DecisionTreeResponse>> getDTRecommendation({
    required String course,
    required String degreeId,
  }) async {
    try {
      final response =
          await _apiClient.recommendationResource.fetchDTRecommendations(
        degreeId: degreeId,
        course: course,
      );

      _logger.d('DT API response: $response');

      if (response.isEmpty) {
        _logger.w('Received empty response from DT recommendations API');
        return [];
      }

      final decodedResponse = jsonDecode(response);

      if (decodedResponse == null) {
        _logger.w('Received null response from DT recommendations API');
        return [];
      }

      final json = decodedResponse as Map<String, dynamic>;
      final recommendation = DecisionTreeResponse.fromJson(json);

      return [recommendation];
    } catch (e) {
      _logger.e(
        'Error fetching rule-based recommendations for course: $course',
        error: e,
      );
      rethrow;
    }
  }

  /// Fetches success probability recommendations for candidate subjects.
  Future<SuccessProbabilityResponse> getCSRecommendations({
    required int studentId,
    required List<String> candidateSubjects,
    required String degreeId,
  }) async {
    try {
      final response =
          await _apiClient.recommendationResource.fetchCSRecommendations(
        studentId: studentId,
        candidateSubjects: candidateSubjects,
        degreeId: degreeId,
      );
      final json = jsonDecode(response) as Map<String, dynamic>;
      final recommendations = SuccessProbabilityResponse.fromJson(json);
      return recommendations;
    } catch (e) {
      _logger.e(
        'Error fetching success probability recommendations '
        'for studentId: $studentId',
        error: e,
      );
      rethrow;
    }
  }

  /// Fetches all path subjects for a given degree.
  Future<List<PathSubject>> getPathSubjects() async {
    try {
      final response = await _apiClient.pathResource.fetchAllSubjects();
      final json = jsonDecode(response) as List<dynamic>;
      final subjects = json
          .map((e) => PathSubject.fromJson(e as Map<String, dynamic>))
          .toList();
      return subjects;
    } catch (e) {
      _logger.e(
        'Error fetching path subjects',
        error: e,
      );
      rethrow;
    }
  }
}
