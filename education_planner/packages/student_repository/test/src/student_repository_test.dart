// ignore_for_file: prefer_const_constructors
import 'package:api_client/api_client.dart';
import 'package:mocktail/mocktail.dart';
import 'package:student_repository/student_repository.dart';
import 'package:test/test.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  group('StudentRepository', () {
    test('can be instantiated', () {
      expect(StudentRepository(client: MockApiClient()), isNotNull);
    });
  });
}
