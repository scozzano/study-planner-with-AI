part of 'schooling_bloc.dart';

enum SchoolingStatus {
  initial,
  loading,
  success,
  loaded,
  error,
  pdfLoading;

  bool get isInitial => this == SchoolingStatus.initial;
  bool get isLoading => this == SchoolingStatus.loading;
  bool get isLoaded => this == SchoolingStatus.loaded;
  bool get isError => this == SchoolingStatus.error;
  bool get isSuccess => this == SchoolingStatus.success;
  bool get isPdfLoading => this == SchoolingStatus.pdfLoading;
}

enum SchoolingStep {
  studentId,
  gradesPdf,
}

class SchoolingState extends Equatable {
  const SchoolingState({
    required this.status,
    required this.schooling,
    required this.gradesPdf,
    required this.studentId,
    required this.step,
  });

  SchoolingState.initial()
      : status = SchoolingStatus.initial,
        schooling = null,
        gradesPdf = PlatformFile(name: '', size: 0),
        studentId = null,
        step = SchoolingStep.studentId;

  final SchoolingStatus status;
  final Schooling? schooling;
  final PlatformFile gradesPdf;
  final String? studentId;
  final SchoolingStep step;

  List<Subject> get displayableSubjects {
    final subjects = schooling?.subjects ?? [];
    if (subjects.isEmpty) return subjects;

    final sortedSubjects = List<Subject>.from(subjects)
      ..sort((a, b) {
        final dateA = a.date;
        final dateB = b.date;

        if (dateA == null && dateB == null) return 0;
        if (dateA == null) return 1;
        if (dateB == null) return -1;

        return dateB.compareTo(dateA);
      });

    final seenCodes = <String>{};
    return sortedSubjects.where((subject) {
      if (seenCodes.contains(subject.code)) {
        return false;
      }
      seenCodes.add(subject.code);
      return true;
    }).toList();
  }

  SchoolingState copyWith({
    SchoolingStatus? status,
    Schooling? schooling,
    PlatformFile? gradesPdf,
    String? studentId,
    SchoolingStep? step,
  }) {
    return SchoolingState(
      status: status ?? this.status,
      schooling: schooling ?? this.schooling,
      gradesPdf: gradesPdf ?? this.gradesPdf,
      studentId: studentId ?? this.studentId,
      step: step ?? this.step,
    );
  }

  @override
  List<Object?> get props => [
        status,
        schooling,
        gradesPdf,
        studentId,
        step,
      ];
}
