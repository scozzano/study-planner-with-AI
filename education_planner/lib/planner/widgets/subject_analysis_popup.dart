import 'package:education_planner/planner/planner.dart';
import 'package:education_planner/schooling/schooling.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:planner_repository/planner_repository.dart';

class SubjectAnalysisPopup extends StatefulWidget {
  const SubjectAnalysisPopup({
    required this.subjects,
    required this.onAnalyze,
    super.key,
  });

  final List<PathSubject> subjects;
  final void Function(PathSubject subject) onAnalyze;

  static Future<void> show(
    BuildContext context, {
    required List<PathSubject> subjects,
    required void Function(PathSubject subject) onAnalyze,
  }) async {
    await showDialog<void>(
      context: context,
      builder: (_) => BlocProvider.value(
        value: context.read<PlannerBloc>(),
        child: SubjectAnalysisPopup(
          subjects: subjects,
          onAnalyze: onAnalyze,
        ),
      ),
    );
  }

  @override
  State<SubjectAnalysisPopup> createState() => _SubjectAnalysisPopupState();
}

class _SubjectAnalysisPopupState extends State<SubjectAnalysisPopup> {
  PathSubject? _selectedSubject;
  final TextEditingController _searchController = TextEditingController();
  List<PathSubject> _filteredSubjects = [];

  @override
  void initState() {
    super.initState();
    _filteredSubjects = widget.subjects;
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _filterSubjects(String query) {
    setState(() {
      if (query.isEmpty) {
        _filteredSubjects = widget.subjects;
      } else {
        _filteredSubjects = widget.subjects
            .where(
              (subject) =>
                  subject.name.toLowerCase().contains(query.toLowerCase()),
            )
            .toList();
      }
    });
  }

  Future<void> _onSubmit() async {
    if (_selectedSubject == null) return;

    widget.onAnalyze(_selectedSubject!);
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = context.select(
      (PlannerBloc bloc) =>
          bloc.state.status == PlannerStatus.fetchingDTRecommendations,
    );
    final recommendedRuleSubjects = context.select(
      (PlannerBloc bloc) => bloc.state.recommendedRuleSubjects,
    );
    return Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        padding: const EdgeInsets.all(24),
        constraints: const BoxConstraints(maxWidth: 500),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _Header(
                onClose: () => Navigator.of(context).pop(),
              ),
              const SizedBox(height: 16),
              if (isLoading)
                const _LoadingContent()
              else if (recommendedRuleSubjects.isEmpty)
                _PreAnalysisContent(
                  searchController: _searchController,
                  filteredSubjects: _filteredSubjects,
                  selectedSubject: _selectedSubject,
                  isLoading: isLoading,
                  onFilterSubjects: _filterSubjects,
                  onSubjectSelected: (subject) {
                    setState(() {
                      _selectedSubject = subject;
                      _searchController.text = subject.name;
                    });
                  },
                  onSubmit: _onSubmit,
                )
              else
                _AnalysisCompletedContent(
                  selectedSubject: _selectedSubject,
                  recommendedRuleSubjects: recommendedRuleSubjects,
                  onAnalyzeAnother: () {
                    setState(() {
                      _selectedSubject = null;
                      _searchController.clear();
                      _filteredSubjects = widget.subjects;
                    });
                  },
                  onClose: () => Navigator.of(context).pop(),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({
    required this.onClose,
  });

  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text(
          'Análisis de Asignatura',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        IconButton(
          onPressed: onClose,
          icon: const Icon(Icons.close),
        ),
      ],
    );
  }
}

class _PreAnalysisContent extends StatelessWidget {
  const _PreAnalysisContent({
    required this.searchController,
    required this.filteredSubjects,
    required this.selectedSubject,
    required this.isLoading,
    required this.onFilterSubjects,
    required this.onSubjectSelected,
    required this.onSubmit,
  });

  final TextEditingController searchController;
  final List<PathSubject> filteredSubjects;
  final PathSubject? selectedSubject;
  final bool isLoading;
  final void Function(String) onFilterSubjects;
  final void Function(PathSubject) onSubjectSelected;
  final Future<void> Function() onSubmit;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Instructions
        const Text(
          'Selecciona una asignatura que te gustaría analizar',
          style: TextStyle(
            fontSize: 16,
            color: Colors.grey,
          ),
        ),
        const SizedBox(height: 24),

        // Search field
        TextField(
          controller: searchController,
          onChanged: onFilterSubjects,
          decoration: InputDecoration(
            hintText: 'Buscar asignatura...',
            prefixIcon: const Icon(Icons.search),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            filled: true,
            fillColor: Colors.grey[50],
          ),
        ),
        const SizedBox(height: 16),

        // Subjects dropdown
        _SubjectsDropdown(
          filteredSubjects: filteredSubjects,
          selectedSubject: selectedSubject,
          onSubjectSelected: onSubjectSelected,
        ),
        const SizedBox(height: 24),

        // Submit button
        _SubmitButton(
          selectedSubject: selectedSubject,
          isLoading: isLoading,
          onSubmit: onSubmit,
        ),
      ],
    );
  }
}

class _SubjectsDropdown extends StatelessWidget {
  const _SubjectsDropdown({
    required this.filteredSubjects,
    required this.selectedSubject,
    required this.onSubjectSelected,
  });

  final List<PathSubject> filteredSubjects;
  final PathSubject? selectedSubject;
  final void Function(PathSubject) onSubjectSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(maxHeight: 200),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey[300]!),
        borderRadius: BorderRadius.circular(12),
      ),
      child: filteredSubjects.isEmpty
          ? const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'No se encontraron asignaturas',
                style: TextStyle(color: Colors.grey),
              ),
            )
          : ListView.builder(
              shrinkWrap: true,
              itemCount: filteredSubjects.length,
              itemBuilder: (context, index) {
                final subject = filteredSubjects[index];
                final isSelected = selectedSubject?.id == subject.id;

                return ListTile(
                  title: Text(subject.name),
                  subtitle: Text('Semestre ${subject.semester}'),
                  selected: isSelected,
                  onTap: () => onSubjectSelected(subject),
                  trailing: isSelected
                      ? const Icon(Icons.check_circle, color: Colors.blue)
                      : null,
                );
              },
            ),
    );
  }
}

class _SubmitButton extends StatelessWidget {
  const _SubmitButton({
    required this.selectedSubject,
    required this.isLoading,
    required this.onSubmit,
  });

  final PathSubject? selectedSubject;
  final bool isLoading;
  final Future<void> Function() onSubmit;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: selectedSubject != null && !isLoading ? onSubmit : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: Theme.of(context).colorScheme.primary,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: isLoading
            ? const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  ),
                  SizedBox(width: 12),
                  Text('Analizando...'),
                ],
              )
            : Text(
                'Analizar',
                style: TextStyle(
                  fontSize: 16,
                  color: Theme.of(context).colorScheme.onPrimary,
                ),
              ),
      ),
    );
  }
}

class _AnalysisCompletedContent extends StatelessWidget {
  const _AnalysisCompletedContent({
    required this.selectedSubject,
    required this.onAnalyzeAnother,
    required this.onClose,
    required this.recommendedRuleSubjects,
  });

  final PathSubject? selectedSubject;
  final VoidCallback onAnalyzeAnother;
  final VoidCallback onClose;
  final List<String> recommendedRuleSubjects;

  @override
  Widget build(BuildContext context) {
    // Get user's approved subjects from schooling data
    final userApprovedSubjects = context
        .select((SchoolingBloc bloc) => bloc.state.schooling?.subjects)
        ?.where((subject) => subject.isApproved)
        .toList();
    final allPathSubjects =
        context.select((PlannerBloc bloc) => bloc.state.allPathSubjects);
    context.select((PlannerBloc bloc) => bloc.state.allPathSubjects);

    final analysisResult = DecisionTreeRuleProcessor.generateAnalysis(
      recommendedRuleSubjects,
      subjects: allPathSubjects,
      targetSubjectName: selectedSubject?.name ?? '',
      userApprovedSubjects: userApprovedSubjects,
    );

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 16),
          _StructuredAnalysisContent(
            analysisResult: analysisResult,
            selectedSubjectName: selectedSubject?.name ?? '',
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

class _LoadingContent extends StatefulWidget {
  const _LoadingContent();

  @override
  State<_LoadingContent> createState() => _LoadingContentState();
}

class _LoadingContentState extends State<_LoadingContent>
    with TickerProviderStateMixin {
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(40),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Loading text
          const Text(
            'Generando análisis',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 8),

          // Animated dots
          _AnimatedDots(animationController: _animationController),
        ],
      ),
    );
  }
}

class _AnimatedDots extends StatelessWidget {
  const _AnimatedDots({
    required this.animationController,
  });

  final AnimationController animationController;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: animationController,
      builder: (context, child) {
        return Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(3, (index) {
            final delay = index * 0.2;
            final animationValue = (animationController.value - delay) % 1.0;
            final opacity = (1.0 - (animationValue * 2)).clamp(0.0, 1.0);

            return Container(
              margin: const EdgeInsets.symmetric(horizontal: 2),
              child: Opacity(
                opacity: opacity,
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: Colors.blue,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            );
          }),
        );
      },
    );
  }
}

class _StructuredAnalysisContent extends StatelessWidget {
  const _StructuredAnalysisContent({
    required this.analysisResult,
    required this.selectedSubjectName,
  });

  final AnalysisResult analysisResult;
  final String selectedSubjectName;

  @override
  Widget build(BuildContext context) {
    if (analysisResult.messages.isEmpty) {
      return const Text('No analysis results available.');
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (analysisResult.hasPersonalizedAnalysis) ...[
          Text(
            'Claves para tu desempeño en $selectedSubjectName:',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 16),
        ],
        ..._sortMessagesByType(analysisResult.messages).map(
          (message) => _AnalysisMessageCard(
            message: message,
          ),
        ),
      ],
    );
  }

  /// Sorts messages by type: success, warning, info, error
  List<AnalysisMessage> _sortMessagesByType(List<AnalysisMessage> messages) {
    final sortedMessages = List<AnalysisMessage>.from(messages)
      ..sort((a, b) {
        // Define priority order: success, warning, info, error
        const typePriority = {
          MessageType.success: 0,
          MessageType.warning: 1,
          MessageType.info: 2,
          MessageType.error: 3,
        };

        final priorityA = typePriority[a.type] ?? 999;
        final priorityB = typePriority[b.type] ?? 999;

        return priorityA.compareTo(priorityB);
      });

    return sortedMessages;
  }
}

class _AnalysisMessageCard extends StatelessWidget {
  const _AnalysisMessageCard({
    required this.message,
  });

  final AnalysisMessage message;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _getBackgroundColor(context),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: _getBorderColor(context),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                _getIcon(),
                color: _getIconColor(context),
                size: 20,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  message.title,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: _getTitleColor(context),
                      ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            message.content,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          if (message.subjects.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 4,
              runSpacing: 4,
              children: message.subjects
                  .map(
                    (subject) => Chip(
                      label: Text(
                        subject,
                        style: TextStyle(
                          fontSize: 12,
                          color: _getChipTextColor(context),
                        ),
                      ),
                      backgroundColor: _getChipBackgroundColor(context),
                      side: BorderSide(
                        color: _getChipBorderColor(context),
                        width: 0.5,
                      ),
                    ),
                  )
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }

  Color _getBackgroundColor(BuildContext context) {
    switch (message.type) {
      case MessageType.success:
        return Colors.green[50]!;
      case MessageType.warning:
        return Colors.orange[50]!;
      case MessageType.info:
        return Colors.blue[50]!;
      case MessageType.error:
        return Colors.red[50]!;
    }
  }

  Color _getBorderColor(BuildContext context) {
    switch (message.type) {
      case MessageType.success:
        return Colors.green[200]!;
      case MessageType.warning:
        return Colors.orange[200]!;
      case MessageType.info:
        return Colors.blue[200]!;
      case MessageType.error:
        return Colors.red[200]!;
    }
  }

  Color _getTitleColor(BuildContext context) {
    switch (message.type) {
      case MessageType.success:
        return Colors.green[700]!;
      case MessageType.warning:
        return Colors.orange[700]!;
      case MessageType.info:
        return Colors.blue[700]!;
      case MessageType.error:
        return Colors.red[700]!;
    }
  }

  Color _getIconColor(BuildContext context) {
    switch (message.type) {
      case MessageType.success:
        return Colors.green[600]!;
      case MessageType.warning:
        return Colors.orange[600]!;
      case MessageType.info:
        return Colors.blue[600]!;
      case MessageType.error:
        return Colors.red[600]!;
    }
  }

  IconData _getIcon() {
    switch (message.type) {
      case MessageType.success:
        return Icons.check_circle;
      case MessageType.warning:
        return Icons.warning;
      case MessageType.info:
        return Icons.info;
      case MessageType.error:
        return Icons.error;
    }
  }

  Color _getChipBackgroundColor(BuildContext context) {
    switch (message.type) {
      case MessageType.success:
        return Colors.green[100]!;
      case MessageType.warning:
        return Colors.orange[100]!;
      case MessageType.info:
        return Colors.blue[100]!;
      case MessageType.error:
        return Colors.red[100]!;
    }
  }

  Color _getChipTextColor(BuildContext context) {
    switch (message.type) {
      case MessageType.success:
        return Colors.green[800]!;
      case MessageType.warning:
        return Colors.orange[800]!;
      case MessageType.info:
        return Colors.blue[800]!;
      case MessageType.error:
        return Colors.red[800]!;
    }
  }

  Color _getChipBorderColor(BuildContext context) {
    switch (message.type) {
      case MessageType.success:
        return Colors.green[300]!;
      case MessageType.warning:
        return Colors.orange[300]!;
      case MessageType.info:
        return Colors.blue[300]!;
      case MessageType.error:
        return Colors.red[300]!;
    }
  }
}
