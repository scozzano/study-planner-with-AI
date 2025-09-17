import 'package:bloc/bloc.dart';
import 'package:education_planner/app/app.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';

part 'app_event.dart';
part 'app_state.dart';

class AppBloc extends Bloc<AppEvent, AppState> {
  AppBloc() : super(AppState.initial()) {
    on<AppStudentIdLoaded>(_onAppStudentIdLoaded);
    on<AppStudentIdRemoved>(_onAppStudentIdRemoved);
  }

  Future<void> _onAppStudentIdLoaded(
    AppStudentIdLoaded event,
    Emitter<AppState> emit,
  ) async {
    final studentId = await SharedPreferencesHelper.getStudentId() ?? '';
    final notifier = state.studentIdNotifier..value = studentId;
    emit(state.copyWith(studentId: studentId, studentIdNotifier: notifier));
  }

  Future<void> _onAppStudentIdRemoved(
    AppStudentIdRemoved event,
    Emitter<AppState> emit,
  ) async {
    await SharedPreferencesHelper.setStudentId('');
    final notifier = state.studentIdNotifier..value = '';
    emit(state.copyWith(studentId: '', studentIdNotifier: notifier));
  }
}
