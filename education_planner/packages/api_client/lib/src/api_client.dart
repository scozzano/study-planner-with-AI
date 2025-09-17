import 'package:api_client/api_client.dart';

/// {@template api_client}
/// A client to communicate with education planner backend
/// {@endtemplate}
class ApiClient {
  /// {@macro api_client}
  ApiClient({
    required HttpApiClient client,
  }) : _client = client;

  final HttpApiClient _client;

  /// {@macro student_resource}
  StudentResource get studentResource {
    return StudentResource(client: _client);
  }

  /// {@macro user_resource}
  UserResource get userResource {
    return UserResource(client: _client);
  }

  /// {@macro path_resource}
  PathResource get pathResource {
    return PathResource(client: _client);
  }

  /// {@macro recommendation_resource}
  RecommendationResource get recommendationResource {
    return RecommendationResource(client: _client);
  }
}
