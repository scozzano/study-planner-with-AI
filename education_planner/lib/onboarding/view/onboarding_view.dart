import 'package:education_planner/app/bloc/app_bloc.dart';
import 'package:education_planner/schooling/schooling.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class OnboardingView extends StatelessWidget {
  const OnboardingView({super.key});

  @override
  Widget build(BuildContext context) {
    final status = context.select((SchoolingBloc bloc) => bloc.state.status);

    return MultiBlocListener(
      listeners: [
        BlocListener<SchoolingBloc, SchoolingState>(
          listenWhen: (previous, current) => previous.status != current.status,
          listener: (context, state) {
            if (state.status.isSuccess) {
              context.read<AppBloc>().add(
                    AppStudentIdLoaded(),
                  );
              context.go(SchoolingPage.path);
            }
          },
        ),
      ],
      child: Scaffold(
        body: status.isLoading
            ? const _LoadingScreen()
            : const Center(
                child: _OnboardingStep(),
              ),
      ),
    );
  }
}

class _LoadingScreen extends StatelessWidget {
  const _LoadingScreen();

  @override
  Widget build(BuildContext context) {
    return const Center(child: CircularProgressIndicator());
  }
}

class _OnboardingStep extends StatelessWidget {
  const _OnboardingStep();

  @override
  Widget build(BuildContext context) {
    final onboardingStep = context.select(
      (SchoolingBloc bloc) => bloc.state.step,
    );
    Widget? content;

    switch (onboardingStep) {
      case SchoolingStep.studentId:
        content = const _StudentIdTextField();
      case SchoolingStep.gradesPdf:
        content = const _GradeFileUpload();
    }
    return Container(
      padding: const EdgeInsets.all(16),
      constraints: const BoxConstraints(
        maxWidth: 400,
        maxHeight: 400,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: content,
    );
  }
}

class _StudentIdTextField extends StatelessWidget {
  const _StudentIdTextField();

  @override
  Widget build(BuildContext context) {
    final continueEnabled = context.select(
      (SchoolingBloc bloc) =>
          bloc.state.studentId != null && bloc.state.studentId!.isNotEmpty,
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        const Text(
          'Ingresa tu número de estudiante',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 18),
        SizedBox(
          child: TextField(
            onChanged: (value) {
              context
                  .read<SchoolingBloc>()
                  .add(SchoolingStudentIdChanged(value));
            },
            keyboardType: TextInputType.number,
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            decoration: const InputDecoration(
              labelText: 'Número de estudiante',
              border: OutlineInputBorder(),
            ),
          ),
        ),
        const SizedBox(height: 18),
        Align(
          alignment: Alignment.bottomRight,
          child: ElevatedButton(
            onPressed: continueEnabled
                ? () {
                    context.read<SchoolingBloc>().add(
                          SchoolingFetchedByStudentId(
                            context.read<SchoolingBloc>().state.studentId!,
                          ),
                        );
                  }
                : null,
            child: const Text('Continuar'),
          ),
        ),
      ],
    );
  }
}

class _GradeFileUpload extends StatelessWidget {
  const _GradeFileUpload();

  @override
  Widget build(BuildContext context) {
    final pdf = context.select(
      (SchoolingBloc bloc) => bloc.state.gradesPdf,
    );
    final isPdfLoading = context.select(
      (SchoolingBloc bloc) => bloc.state.status.isPdfLoading,
    );
    final continueEnabled = context.select(
      (SchoolingBloc bloc) =>
          bloc.state.gradesPdf.size > 0 &&
          bloc.state.studentId != null &&
          bloc.state.studentId!.isNotEmpty,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        const Text(
          'Ingresa tu escolaridad para poder continuar',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 18),
        Container(
          height: 200,
          width: 400,
          decoration: BoxDecoration(
            border: Border.all(color: Colors.grey),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (isPdfLoading)
                const CircularProgressIndicator()
              else if (pdf.size > 0) ...[
                const Icon(
                  Icons.file_download_done,
                  size: 40,
                  color: Colors.green,
                ),
                const Text(
                  'Archivo seleccionado',
                  style: TextStyle(
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  pdf.name,
                  style: const TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 10),
                ElevatedButton.icon(
                  onPressed: () {
                    context.read<SchoolingBloc>().add(
                          const SchoolingPdfChanged(filePickerResult: null),
                        );
                  },
                  icon: const Icon(Icons.delete),
                  label: const Text('Eliminar'),
                ),
              ] else if (pdf.size == 0) ...[
                const Icon(Icons.cloud_upload_outlined, size: 40),
                const Text(
                  'Escoge el pdf o arrastralo aquí',
                  style: TextStyle(
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 10),
                ElevatedButton.icon(
                  onPressed: () async {
                    final result = await FilePicker.platform.pickFiles(
                      type: FileType.custom,
                      allowedExtensions: ['pdf'],
                    );
                    if (context.mounted && result != null) {
                      context.read<SchoolingBloc>().add(
                            SchoolingPdfChanged(
                              filePickerResult: result,
                            ),
                          );
                    }
                  },
                  label: const Text('Seleccionar'),
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: 18),
        Align(
          alignment: Alignment.bottomRight,
          child: ElevatedButton(
            onPressed: continueEnabled
                ? () {
                    context.read<SchoolingBloc>().add(
                          const SchoolingSubmitButtonPressed(),
                        );
                  }
                : null,
            child: const Text('Continuar'),
          ),
        ),
      ],
    );
  }
}
