part of 'app_bloc.dart';

class AppState extends Equatable {
  const AppState({
    required this.studentId,
    required this.studentIdNotifier,
  });

  AppState.initial()
      : studentId = '',
        studentIdNotifier = ValueNotifier<String>('');

  final String studentId;
  final ValueNotifier<String> studentIdNotifier;

  AppState copyWith({
    String? studentId,
    ValueNotifier<String>? studentIdNotifier,
  }) {
    return AppState(
      studentId: studentId ?? this.studentId,
      studentIdNotifier: studentIdNotifier ?? this.studentIdNotifier,
    );
  }

  @override
  List<Object> get props => [
        studentId,
        studentIdNotifier,
      ];
}
