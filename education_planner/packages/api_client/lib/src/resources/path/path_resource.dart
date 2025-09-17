import 'package:api_client/api_client.dart';
import 'package:logger/logger.dart';

/// {@template path_resource}
/// A client to communicate with the path resource.
/// {@endtemplate}
class PathResource {
  /// {@macro path_resource}
  PathResource({
    required HttpApiClient client,
  }) : _client = client;

  final HttpApiClient _client;
  final _logger = Logger();
  static const String _basePath = '/university';
  static String _degreeRecommendedPath(String degreeId) =>
      '$_basePath/$degreeId';

  /// Fetches the recommended path for a given degree.
  Future<String> fetchDegreeRecommendedPath({required String degreeId}) async {
    try {
      final response = await _client.get(
        _degreeRecommendedPath(degreeId),
      );
      return response.body;
    } catch (e) {
      _logger.e(
        'Error fetching degree recommended path for degreeId: $degreeId',
        error: e,
      );
      rethrow;
    }
  }

  /// Fetches all subjects for a given degree.
  Future<String> fetchAllSubjects() async {
    try {
      final response = await _client.get(
        '$_basePath/subjects',
      );
      return response.body;
    } catch (e) {
      _logger.e(
        'Error fetching all subjects',
        error: e,
      );
      rethrow;
    }
  }
}
