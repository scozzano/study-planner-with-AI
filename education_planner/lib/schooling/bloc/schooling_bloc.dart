import 'dart:async';
import 'dart:convert';

import 'package:api_client/api_client.dart';
import 'package:bloc/bloc.dart';
import 'package:education_planner/app/app.dart';
import 'package:education_planner/constants.dart';
import 'package:equatable/equatable.dart';
import 'package:file_picker/file_picker.dart';
import 'package:student_repository/student_repository.dart';

part 'schooling_event.dart';
part 'schooling_state.dart';

class SchoolingBloc extends Bloc<SchoolingEvent, SchoolingState> {
  SchoolingBloc({
    required StudentRepository studentRepository,
  })  : _studentRepository = studentRepository,
        super(SchoolingState.initial()) {
    on<SchoolingPdfChanged>(_onSchoolingPdfChanged);
    on<SchoolingStudentIdChanged>(_onSchoolingStudentIdChanged);
    on<SchoolingSubmitButtonPressed>(_onSchoolingSubmitButtonPressed);
    on<SchoolingFetched>(_onSchoolingFetched);
    on<SchoolingFetchedByStudentId>(_onSchoolingFetchedByStudentId);
  }

  final StudentRepository _studentRepository;

  FutureOr<void> _onSchoolingPdfChanged(
    SchoolingPdfChanged event,
    Emitter<SchoolingState> emit,
  ) async {
    try {
      if (event.filePickerResult == null) {
        emit(state.copyWith(gradesPdf: PlatformFile(name: '', size: 0)));
        return;
      }
      emit(state.copyWith(status: SchoolingStatus.pdfLoading));

      final file = event.filePickerResult?.files.first;

      emit(
        state.copyWith(
          status: SchoolingStatus.loaded,
          gradesPdf: file,
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: SchoolingStatus.error));
    }
  }

  FutureOr<void> _onSchoolingStudentIdChanged(
    SchoolingStudentIdChanged event,
    Emitter<SchoolingState> emit,
  ) async {
    try {
      emit(
        state.copyWith(
          studentId: event.studentId,
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: SchoolingStatus.error));
    }
  }

  FutureOr<void> _onSchoolingSubmitButtonPressed(
    SchoolingSubmitButtonPressed event,
    Emitter<SchoolingState> emit,
  ) async {
    try {
      emit(state.copyWith(status: SchoolingStatus.loading));

      if (state.gradesPdf.size == 0 ||
          state.studentId == null ||
          state.studentId!.isEmpty) {
        emit(state.copyWith(status: SchoolingStatus.error));
        return;
      }

      final fileBytes = state.gradesPdf.bytes;
      final fileEncoded = base64Encode(fileBytes!);
      await _studentRepository.submitSchoolingPdf(
        pdf: fileEncoded,
      );

      await SharedPreferencesHelper.setStudentId(state.studentId!);

      emit(state.copyWith(status: SchoolingStatus.success));
    } catch (e) {
      emit(state.copyWith(status: SchoolingStatus.error));
    }
  }

  FutureOr<void> _onSchoolingFetched(
    SchoolingFetched event,
    Emitter<SchoolingState> emit,
  ) async {
    emit(state.copyWith(status: SchoolingStatus.loading));
    try {
      final studentId = await SharedPreferencesHelper.getStudentId() ?? '';

      if (studentId.isEmpty) {
        emit(
          state.copyWith(
            step: SchoolingStep.studentId,
            status: SchoolingStatus.loaded,
          ),
        );
        return;
      }

      final schooling = await _studentRepository.fetchSchooling(
        studentId: studentId,
        degreeId: Constants.kSystemsDegreeId,
      );

      emit(
        state.copyWith(
          status: SchoolingStatus.loaded,
          schooling: schooling,
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: SchoolingStatus.error));
    }
  }

  FutureOr<void> _onSchoolingFetchedByStudentId(
    SchoolingFetchedByStudentId event,
    Emitter<SchoolingState> emit,
  ) async {
    emit(state.copyWith(status: SchoolingStatus.loading));
    try {
      final studentId = event.studentId;

      if (studentId.isEmpty) {
        emit(
          state.copyWith(
            step: SchoolingStep.studentId,
            status: SchoolingStatus.loaded,
          ),
        );
        return;
      }

      final schooling = await _studentRepository.fetchSchooling(
        studentId: event.studentId,
        degreeId: Constants.kSystemsDegreeId,
      );

      await SharedPreferencesHelper.setStudentId(event.studentId);

      emit(
        state.copyWith(
          status: SchoolingStatus.success,
          schooling: schooling,
        ),
      );
    } on SchoolingNotFoundException {
      emit(
        state.copyWith(
          step: SchoolingStep.gradesPdf,
          status: SchoolingStatus.loaded,
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: SchoolingStatus.error));
    }
  }
}
