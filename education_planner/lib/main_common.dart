import 'package:api_client/api_client.dart';
import 'package:auth_client/auth_client.dart';
import 'package:education_planner/app/app.dart';
import 'package:planner_repository/planner_repository.dart';
import 'package:student_repository/student_repository.dart';

Future<App> mainCommon({
  required String apiUrl,
}) async {
  final httpClient = HttpApiClient(
    apiUrl: apiUrl,
    apiKey: '',
    tokenProvider: AuthenticationClient(),
  );
  final apiClient = ApiClient(client: httpClient);
  final studentRepository = StudentRepository(client: apiClient);
  final plannerRepository = PlannerRepository(apiClient: apiClient);

  return App(
    studentRepository: studentRepository,
    plannerRepository: plannerRepository,
  );
}
