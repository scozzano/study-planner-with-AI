part of 'app_bloc.dart';

class AppEvent extends Equatable {
  const AppEvent();

  @override
  List<Object> get props => [];
}

class AppStudentIdLoaded extends AppEvent {}

class AppStudentIdRemoved extends AppEvent {}
