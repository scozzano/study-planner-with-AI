part of 'planner_bloc.dart';

class PlannerEvent extends Equatable {
  const PlannerEvent();

  @override
  List<Object?> get props => [];
}

class PlannerDegreePathRequested extends PlannerEvent {
  const PlannerDegreePathRequested({
    required this.degreeId,
  });

  final String degreeId;

  @override
  List<Object> get props => [degreeId];
}

class PlannerDrawerChanged extends PlannerEvent {
  const PlannerDrawerChanged({
    this.semesterTarget,
  });

  final Semester? semesterTarget;

  @override
  List<Object?> get props => [semesterTarget];
}

class PlannerSubjectSelected extends PlannerEvent {
  const PlannerSubjectSelected({
    required this.subject,
  });

  final PathSubject subject;

  @override
  List<Object> get props => [subject];
}

class PlannerSubjectsSubmitted extends PlannerEvent {
  const PlannerSubjectsSubmitted();

  @override
  List<Object> get props => [];
}

class PlannerSubjectChanged extends PlannerEvent {
  const PlannerSubjectChanged({
    required this.updatedSemester,
  });

  final SelectedSemester updatedSemester;

  @override
  List<Object> get props => [updatedSemester];
}

class PlannerSubjectRemoved extends PlannerEvent {
  const PlannerSubjectRemoved({
    required this.updatedSemester,
  });

  final SelectedSemester updatedSemester;

  @override
  List<Object> get props => [updatedSemester];
}

class PlannerSubjectRecomendationsForSemesterFetched extends PlannerEvent {
  const PlannerSubjectRecomendationsForSemesterFetched({
    required this.semester,
  });

  final Semester semester;

  @override
  List<Object> get props => [semester];
}

class PlannerSubjectAnalysisRequested extends PlannerEvent {
  const PlannerSubjectAnalysisRequested({
    required this.subject,
  });

  final PathSubject subject;

  @override
  List<Object> get props => [subject];
}
