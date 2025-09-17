import 'package:education_planner/schooling/schooling.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import 'package:student_repository/student_repository.dart';

class SchoolingView extends StatelessWidget {
  const SchoolingView({super.key});

  @override
  Widget build(BuildContext context) {
    final status = context.select((SchoolingBloc bloc) => bloc.state.status);
    final subjects = context.select(
      (SchoolingBloc bloc) => bloc.state.displayableSubjects,
    );

    return status.isLoading
        ? const Center(child: CircularProgressIndicator())
        : Padding(
            padding: const EdgeInsets.all(16),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Mi Escolaridad',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).colorScheme.onSurface,
                        ),
                  ),
                  const SizedBox(height: 8),
                  const SizedBox(height: 24),
                  _SchoolingInfoCard(
                    schooling: context.select(
                      (SchoolingBloc bloc) => bloc.state.schooling,
                    ),
                  ),
                  const SizedBox(height: 16),
                  SingleChildScrollView(
                    child: _SchoolingTable(subjects: subjects),
                  ),
                ],
              ),
            ),
          );
  }
}

class _SchoolingTable extends StatelessWidget {
  const _SchoolingTable({required this.subjects});

  final List<Subject> subjects;

  @override
  Widget build(BuildContext context) {
    if (subjects.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.school_outlined,
              size: 64,
              color: Theme.of(context)
                  .colorScheme
                  .onSurface
                  .withValues(alpha: 0.3),
            ),
            const SizedBox(height: 16),
            Text(
              'No hay materias registradas',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Theme.of(context)
                        .colorScheme
                        .onSurface
                        .withValues(alpha: 0.6),
                  ),
            ),
          ],
        ),
      );
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        // Calculate column widths based on available space
        final availableWidth = constraints.maxWidth - 32; // Account for padding
        const spacing = 8.0;
        const totalSpacing = spacing * 5; // 5 gaps between 6 columns
        final usableWidth = availableWidth - totalSpacing;

        // Define column width ratios (code:name:semester:status:grade:date)
        const codeRatio = 0.12; // 12% for code
        const semesterRatio = 0.10; // 10% for semester
        const statusRatio = 0.12; // 12% for status
        const gradeRatio = 0.13; // 13% for grade
        const dateRatio = 0.13; // 13% for date

        final codeWidth = usableWidth * codeRatio;
        final semesterWidth = usableWidth * semesterRatio;
        final statusWidth = usableWidth * statusRatio;
        final gradeWidth = usableWidth * gradeRatio;
        final dateWidth = usableWidth * dateRatio;

        return Card(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              // Header
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Theme.of(context)
                      .colorScheme
                      .primaryContainer
                      .withValues(alpha: 0.3),
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(12),
                    topRight: Radius.circular(12),
                  ),
                ),
                child: Row(
                  children: [
                    SizedBox(
                      width: codeWidth,
                      child: Text(
                        'Código',
                        style: Theme.of(context)
                            .textTheme
                            .labelMedium
                            ?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: Theme.of(context).colorScheme.onSurface,
                            ),
                      ),
                    ),
                    const SizedBox(width: spacing),
                    Expanded(
                      child: Text(
                        'Nombre',
                        style: Theme.of(context)
                            .textTheme
                            .labelMedium
                            ?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: Theme.of(context).colorScheme.onSurface,
                            ),
                      ),
                    ),
                    const SizedBox(width: spacing),
                    SizedBox(
                      width: semesterWidth,
                      child: Text(
                        'Semestre',
                        style: Theme.of(context)
                            .textTheme
                            .labelMedium
                            ?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: Theme.of(context).colorScheme.onSurface,
                            ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(width: spacing),
                    SizedBox(
                      width: statusWidth,
                      child: Text(
                        'Estado',
                        style: Theme.of(context)
                            .textTheme
                            .labelMedium
                            ?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: Theme.of(context).colorScheme.onSurface,
                            ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(width: spacing),
                    SizedBox(
                      width: gradeWidth,
                      child: Text(
                        'Calificación',
                        style: Theme.of(context)
                            .textTheme
                            .labelMedium
                            ?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: Theme.of(context).colorScheme.onSurface,
                            ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(width: spacing),
                    SizedBox(
                      width: dateWidth,
                      child: Text(
                        'Fecha',
                        style: Theme.of(context)
                            .textTheme
                            .labelMedium
                            ?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: Theme.of(context).colorScheme.onSurface,
                            ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),
              // Rows
              ...subjects.asMap().entries.map((entry) {
                final index = entry.key;
                final subject = entry.value;
                final isEven = index.isEven;

                return Container(
                  decoration: BoxDecoration(
                    color: isEven
                        ? Colors.transparent
                        : Theme.of(context)
                            .colorScheme
                            .surface
                            .withValues(alpha: 0.3),
                  ),
                  child: _SubjectRow(
                    subject: subject,
                    codeWidth: codeWidth,
                    semesterWidth: semesterWidth,
                    statusWidth: statusWidth,
                    gradeWidth: gradeWidth,
                    dateWidth: dateWidth,
                    spacing: spacing,
                  ),
                );
              }),
            ],
          ),
        );
      },
    );
  }
}

class _SubjectRow extends StatelessWidget {
  const _SubjectRow({
    required this.subject,
    required this.codeWidth,
    required this.semesterWidth,
    required this.statusWidth,
    required this.gradeWidth,
    required this.dateWidth,
    required this.spacing,
  });

  final Subject subject;
  final double codeWidth;
  final double semesterWidth;
  final double statusWidth;
  final double gradeWidth;
  final double dateWidth;
  final double spacing;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          // Código
          SizedBox(
            width: codeWidth,
            child: Text(
              subject.code,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.primary,
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ),
          SizedBox(width: spacing),
          // Nombre
          Expanded(
            child: Text(
              subject.name,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          SizedBox(width: spacing),
          // Semestre
          SizedBox(
            width: semesterWidth,
            child: Text(
              subject.semester,
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
          ),
          SizedBox(width: spacing),
          // Estado
          SizedBox(
            width: statusWidth,
            child: _CompactStatusChip(status: subject.status),
          ),
          SizedBox(width: spacing),
          // Nota
          SizedBox(
            width: gradeWidth,
            child: Text(
              subject.grade?.toString() ?? '-',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: _getGradeColor(context, subject.grade),
                  ),
              textAlign: TextAlign.center,
            ),
          ),
          SizedBox(width: spacing),
          // Fecha
          SizedBox(
            width: dateWidth,
            child: Text(
              DateFormat('dd/MM/yyyy').format(subject.date ?? DateTime.now()),
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    );
  }

  Color _getGradeColor(BuildContext context, int? grade) {
    if (grade == null) return Theme.of(context).colorScheme.onSurface;
    if (grade >= 7) return Colors.green.shade700;
    if (grade >= 4) return Colors.orange.shade700;
    return Colors.red.shade700;
  }
}

class _CompactStatusChip extends StatelessWidget {
  const _CompactStatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    Color backgroundColor;
    Color textColor;
    var text = status;

    switch (status.toUpperCase()) {
      case 'APR':
        backgroundColor = Colors.green.withValues(alpha: 0.1);
        textColor = Colors.green.shade700;
        text = 'Aprobado';
      case 'ELI':
        backgroundColor = Colors.red.withValues(alpha: 0.1);
        textColor = Colors.red.shade700;
        text = 'Eliminado';
      case 'CUR':
        backgroundColor = Colors.blue.withValues(alpha: 0.1);
        textColor = Colors.blue.shade700;
        text = 'En curso';
      default:
        backgroundColor = Colors.grey.withValues(alpha: 0.1);
        textColor = Colors.grey.shade700;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: textColor,
          fontWeight: FontWeight.w600,
          fontSize: 10,
        ),
        textAlign: TextAlign.center,
      ),
    );
  }
}

class _SchoolingInfoCard extends StatelessWidget {
  const _SchoolingInfoCard({required this.schooling});

  final Schooling? schooling;

  @override
  Widget build(BuildContext context) {
    if (schooling == null) {
      return const SizedBox.shrink();
    }
    final subjectsObtained = schooling!.subjectsObtained;
    final subjectsRequired = schooling!.subjectsRequired;
    final progress =
        '${((subjectsObtained / subjectsRequired) * 100).toStringAsFixed(1)}%';

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Icon(
                  Icons.school_outlined,
                  color: Theme.of(context).colorScheme.primary,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Text(
                  'Información Académica',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Theme.of(context).colorScheme.onSurface,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Compact row layout
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Basic Information
                  _CompactInfoSection(
                    title: 'Básica',
                    children: [
                      _CompactInfoRow(
                        label: 'Nombre',
                        value: schooling!.name ?? 'No especificado',
                      ),
                      _CompactInfoRow(
                        label: 'Título',
                        value: schooling!.title ?? 'No especificado',
                      ),
                      _CompactInfoRow(
                        label: 'Plan',
                        value: schooling!.plan ?? 'No especificado',
                      ),
                    ],
                  ),

                  const SizedBox(width: 24),

                  // Dates
                  _CompactInfoSection(
                    title: 'Fechas',
                    children: [
                      _CompactInfoRow(
                        label: 'Inicio',
                        value: schooling!.startDate != null
                            ? DateFormat('dd/MM/yyyy')
                                .format(schooling!.startDate!)
                            : 'No especificado',
                      ),
                      _CompactInfoRow(
                        label: 'Graduación',
                        value: schooling!.graduationDate != null
                            ? DateFormat('dd/MM/yyyy')
                                .format(schooling!.graduationDate!)
                            : 'En curso',
                      ),
                    ],
                  ),

                  const SizedBox(width: 24),

                  // Academic Performance
                  _CompactInfoSection(
                    title: 'Promedios',
                    children: [
                      _CompactInfoRow(
                        label: 'General',
                        value: '${schooling!.averageGrade}',
                        valueColor:
                            _getGradeColor(context, schooling!.averageGrade),
                      ),
                      _CompactInfoRow(
                        label: 'Aprobado',
                        value: '${schooling!.averageApprovedGrade}',
                        valueColor: _getGradeColor(
                          context,
                          schooling!.averageApprovedGrade,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(width: 24),

                  // Subject Statistics
                  _CompactInfoSection(
                    title: 'Materias',
                    children: [
                      _CompactInfoRow(
                        label: 'Requeridas',
                        value: '${schooling!.subjectsRequired}',
                      ),
                      _CompactInfoRow(
                        label: 'Obtenidas',
                        value: '${schooling!.subjectsObtained}',
                        valueColor: Colors.green.shade700,
                      ),
                      _CompactInfoRow(
                        label: 'Reprobadas',
                        value: '${schooling!.failedSubjects}',
                        valueColor: Colors.red.shade700,
                      ),
                      _CompactInfoRow(
                        label: 'Progreso',
                        value: progress,
                        valueColor: _getProgressColor(
                          context,
                          schooling!.subjectsObtained,
                          schooling!.subjectsRequired,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getGradeColor(BuildContext context, int grade) {
    if (grade >= 7) return Colors.green.shade700;
    if (grade >= 4) return Colors.orange.shade700;
    return Colors.red.shade700;
  }

  Color _getProgressColor(BuildContext context, int obtained, int required) {
    final percentage = obtained / required;
    if (percentage >= 0.8) return Colors.green.shade700;
    if (percentage >= 0.6) return Colors.orange.shade700;
    return Colors.red.shade700;
  }
}

class _CompactInfoSection extends StatelessWidget {
  const _CompactInfoSection({
    required this.title,
    required this.children,
  });

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w600,
                color: Theme.of(context).colorScheme.primary,
              ),
        ),
        const SizedBox(height: 6),
        ...children,
      ],
    );
  }
}

class _CompactInfoRow extends StatelessWidget {
  const _CompactInfoRow({
    required this.label,
    required this.value,
    this.valueColor,
  });

  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$label: ',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w500,
                  color: Theme.of(context)
                      .colorScheme
                      .onSurface
                      .withValues(alpha: 0.7),
                ),
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: valueColor ?? Theme.of(context).colorScheme.onSurface,
                ),
          ),
        ],
      ),
    );
  }
}
