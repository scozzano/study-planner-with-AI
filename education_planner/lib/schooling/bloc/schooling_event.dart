part of 'schooling_bloc.dart';

class SchoolingEvent extends Equatable {
  const SchoolingEvent();

  @override
  List<Object?> get props => [];
}

class SchoolingPdfChanged extends SchoolingEvent {
  const SchoolingPdfChanged({required this.filePickerResult});

  final FilePickerResult? filePickerResult;

  @override
  List<Object?> get props => [filePickerResult];
}

class SchoolingStudentIdChanged extends SchoolingEvent {
  const SchoolingStudentIdChanged(this.studentId);

  final String studentId;

  @override
  List<Object?> get props => [studentId];
}

class SchoolingSubmitButtonPressed extends SchoolingEvent {
  const SchoolingSubmitButtonPressed();
}

class SchoolingFetched extends SchoolingEvent {
  const SchoolingFetched();

  @override
  List<Object?> get props => [];
}

class SchoolingFetchedByStudentId extends SchoolingEvent {
  const SchoolingFetchedByStudentId(this.studentId);

  final String studentId;

  @override
  List<Object?> get props => [studentId];
}
