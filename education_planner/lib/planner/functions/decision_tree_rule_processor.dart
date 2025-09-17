import 'package:collection/collection.dart';
import 'package:equatable/equatable.dart';
import 'package:planner_repository/planner_repository.dart';
import 'package:student_repository/student_repository.dart';

// ============================================================================
// DATA STRUCTURES FOR STRUCTURED MESSAGES
// ============================================================================

enum MessageType {
  success,
  warning,
  info,
  error,
}

class AnalysisMessage extends Equatable {
  const AnalysisMessage({
    required this.type,
    required this.title,
    required this.content,
    required this.subjects,
  });

  final MessageType type;
  final String title;
  final String content;
  final List<String> subjects;

  @override
  List<Object?> get props => [type, title, content, subjects];
}

class AnalysisResult extends Equatable {
  const AnalysisResult({
    required this.messages,
    required this.hasPersonalizedAnalysis,
  });

  final List<AnalysisMessage> messages;
  final bool hasPersonalizedAnalysis;

  @override
  List<Object?> get props => [messages, hasPersonalizedAnalysis];
}

class RuleWithConfidence extends Equatable {
  const RuleWithConfidence({
    required this.ruleString,
    required this.confidence,
  });

  final String ruleString;
  final double confidence;

  @override
  List<Object?> get props => [ruleString, confidence];
}

/// Processes DecisionTreeRule objects into UI-friendly text
class DecisionTreeRuleProcessor {
  /// Minimum confidence threshold for rule processing (80%)
  static const double minConfidenceThreshold = 80;

  /// Extracts rule strings and confidence
  /// values from the decision tree response
  static List<RuleWithConfidence> extractRulesWithConfidence(
    List<dynamic> ruleData,
  ) {
    final rulesWithConfidence = <RuleWithConfidence>[];

    for (final item in ruleData) {
      if (item is String) {
        // Parse the string representation of the array
        final parsedRules = _parseRuleStringWithConfidence(item);
        rulesWithConfidence.addAll(parsedRules);
      } else if (item is List && item.isNotEmpty) {
        // Extract rule string and confidence
        final ruleParts = <String>[];
        double? confidence;

        // First pass: collect all string parts to build the rule
        for (var i = 0; i < item.length; i++) {
          final element = item[i];
          if (element is String) {
            ruleParts.add(element);
          } else if (element is num) {
            // First numeric element is confidence
            confidence ??= element.toDouble();
            break; // Stop after getting confidence
          }
        }

        if (ruleParts.isNotEmpty) {
          rulesWithConfidence.add(
            RuleWithConfidence(
              ruleString: ruleParts.join(', '),
              confidence: confidence ?? 0.0,
            ),
          );
        }
      }
    }

    return rulesWithConfidence;
  }

  /// Extracts rule strings from the decision tree
  /// response (legacy method for backward compatibility)
  static List<String> extractRuleStrings(List<dynamic> ruleData) {
    return extractRulesWithConfidence(ruleData)
        .map((rule) => rule.ruleString)
        .toList();
  }

  /// Filters rules by minimum confidence threshold
  static List<RuleWithConfidence> filterRulesByConfidence(
    List<RuleWithConfidence> rules,
    double minConfidence,
  ) {
    return rules.where((rule) => rule.confidence >= minConfidence).toList();
  }

  /// Gets the top N rules by confidence
  static List<RuleWithConfidence> getTopRulesByConfidence(
    List<RuleWithConfidence> rules,
    int count,
  ) {
    final sortedRules = List<RuleWithConfidence>.from(rules)
      ..sort((a, b) => b.confidence.compareTo(a.confidence));
    return sortedRules.take(count).toList();
  }

  /// Filters rules by the minimum confidence threshold
  static List<RuleWithConfidence> filterByMinConfidence(
    List<RuleWithConfidence> rules,
  ) {
    return rules
        .where((rule) => rule.confidence >= minConfidenceThreshold)
        .toList();
  }

  /// Parses a string representation of rule arrays
  /// to extract individual rule strings with confidence
  static List<RuleWithConfidence> _parseRuleStringWithConfidence(
    String ruleString,
  ) {
    final rulesWithConfidence = <RuleWithConfidence>[];

    // Remove outer brackets and split by array boundaries
    final cleanString = ruleString.replaceAll(RegExp(r'^\[|\]$'), '');

    // Split by '], [' to separate individual rule arrays
    final ruleArrays = cleanString.split('], [');

    for (final ruleArray in ruleArrays) {
      // Clean up the rule array string
      final cleanRuleArray = ruleArray.replaceAll(RegExp(r'^\[|\]$'), '');

      // Split by comma to get individual elements
      final elements = cleanRuleArray.split(', ');

      // Extract rule parts (strings before the first numeric value)
      final ruleParts = <String>[];
      double? confidence;

      for (var i = 0; i < elements.length; i++) {
        final element = elements[i].trim();

        // Check if this is a numeric value (starts with digit or is a number)
        if (RegExp(r'^\d+(\.\d+)?$').hasMatch(element)) {
          // First numeric element is confidence
          confidence ??= double.tryParse(element) ?? 0.0;
          // Hit a numeric value, stop processing
          break;
        } else if (element.startsWith('[')) {
          // Hit an array, stop processing
          break;
        }

        // Add the rule part
        ruleParts.add(element);
      }

      if (ruleParts.isNotEmpty) {
        rulesWithConfidence.add(
          RuleWithConfidence(
            ruleString: ruleParts.join(', '),
            confidence: confidence ?? 0.0,
          ),
        );
      }
    }

    return rulesWithConfidence;
  }

  /// Generates structured analysis from decision tree rules
  static AnalysisResult generateAnalysis(
    List<dynamic> ruleData, {
    required List<PathSubject> subjects,
    required String targetSubjectName,
    List<Subject>? userApprovedSubjects,
  }) {
    if (ruleData.isEmpty) {
      return const AnalysisResult(
        messages: [],
        hasPersonalizedAnalysis: false,
      );
    }

    final rulesWithConfidence = extractRulesWithConfidence(ruleData);

    if (rulesWithConfidence.isEmpty) {
      return const AnalysisResult(
        messages: [],
        hasPersonalizedAnalysis: false,
      );
    }

    // Sort rules by confidence (highest first) and process them
    final sortedRules = rulesWithConfidence
      ..sort((a, b) => b.confidence.compareTo(a.confidence));

    // Filter rules with confidence >= 80%
    final highConfidenceRules = sortedRules
        .where((rule) => rule.confidence >= minConfidenceThreshold)
        .toList();

    final processedRules = highConfidenceRules
        .map(
          (rule) => RuleProcessed.fromString(
            rule.ruleString,
            subjects,
            confidence: rule.confidence,
          ),
        )
        .toList();

    final mergedRules =
        _mergeRulesByClassCondition(processedRules).toSet().toList();
    final groupedRules = groupRulesByClassCondition(mergedRules);

    final messages = <AnalysisMessage>[];
    final hasPersonalizedAnalysis =
        userApprovedSubjects != null && userApprovedSubjects.isNotEmpty;

    // Process good conditions (prioritize high confidence rules)
    final goodRules = groupedRules[PerformanceOutcome.good] ?? [];
    if (goodRules.isNotEmpty) {
      // Sort good rules by confidence and take top ones
      final sortedGoodRules = goodRules
        ..sort((a, b) => b.confidence.compareTo(a.confidence));

      final goodMessages = processGoodConditions(
        sortedGoodRules,
        userApprovedSubjects ?? [],
        targetSubjectName,
      );
      messages.addAll(goodMessages);
    }

    // Process poor conditions (prioritize high confidence rules)
    final poorRules = groupedRules[PerformanceOutcome.poor] ?? [];
    if (poorRules.isNotEmpty) {
      // Sort poor rules by confidence and take top ones
      final sortedPoorRules = poorRules
        ..sort((a, b) => b.confidence.compareTo(a.confidence));

      final poorMessages = processPoorConditions(
        sortedPoorRules,
        userApprovedSubjects ?? [],
        targetSubjectName,
      );
      messages.addAll(poorMessages);
    }

    // Add general analysis if no specific patterns found
    if (goodRules.isEmpty && poorRules.isEmpty) {
      messages.add(
        AnalysisMessage(
          type: MessageType.info,
          title: 'Análisis General',
          content: 'El análisis de $targetSubjectName muestra patrones '
              'complejos en el rendimiento estudiantil.',
          subjects: const [],
        ),
      );
    }

    return AnalysisResult(
      messages: messages,
      hasPersonalizedAnalysis: hasPersonalizedAnalysis,
    );
  }

  /// Converts decision tree rules to user-friendly text for UI display
  static String generateUIText(
    List<dynamic> ruleData, {
    required List<PathSubject> subjects,
    required String targetSubjectName,
    List<Subject>? userApprovedSubjects,
  }) {
    if (ruleData.isEmpty) {
      return 'No analysis results available.';
    }

    final buffer = StringBuffer();

    // Extract rule strings with confidence from the decision tree response
    final rulesWithConfidence = extractRulesWithConfidence(ruleData);

    if (rulesWithConfidence.isEmpty) {
      return 'No valid rule strings found in the response. Debug: $ruleData';
    }

    // Sort rules by confidence (highest first) and process them
    final sortedRules = rulesWithConfidence
      ..sort((a, b) => b.confidence.compareTo(a.confidence));

    // Filter rules with confidence >= 80%
    final highConfidenceRules = sortedRules
        .where((rule) => rule.confidence >= minConfidenceThreshold)
        .toList();

    // Process the rules
    final processedRules = highConfidenceRules
        .map(
          (rule) => RuleProcessed.fromString(
            rule.ruleString,
            subjects,
            confidence: rule.confidence,
          ),
        )
        .toList();

    // Group and merge rules by classCondition
    final mergedRules =
        _mergeRulesByClassCondition(processedRules).toSet().toList();
    final groupedRules = groupRulesByClassCondition(mergedRules);

    // Add cross-validation analysis if user data is available
    if (userApprovedSubjects != null && userApprovedSubjects.isNotEmpty) {
      buffer
        ..writeln(
          'Análisis personalizado basado en tu rendimiento académico:',
        )
        ..writeln();
    }

    // Process good conditions (prioritize high confidence rules)
    final goodRules = groupedRules[PerformanceOutcome.good] ?? [];
    if (goodRules.isNotEmpty) {
      // Sort good rules by confidence and take top ones
      final sortedGoodRules = goodRules
        ..sort((a, b) => b.confidence.compareTo(a.confidence));

      final goodAnalysis = processGoodConditions(
        sortedGoodRules,
        userApprovedSubjects ?? [],
        targetSubjectName,
      );
      if (goodAnalysis.isNotEmpty) {
        buffer
          ..writeln('Patrones de éxito identificados:')
          ..writeln(goodAnalysis);
      }
    }

    // Process poor conditions (prioritize high confidence rules)
    final poorRules = groupedRules[PerformanceOutcome.poor] ?? [];
    if (poorRules.isNotEmpty) {
      // Sort poor rules by confidence and take top ones
      final sortedPoorRules = poorRules
        ..sort((a, b) => b.confidence.compareTo(a.confidence));

      final poorAnalysis = processPoorConditions(
        sortedPoorRules,
        userApprovedSubjects ?? [],
        targetSubjectName,
      );
      if (poorAnalysis.isNotEmpty) {
        buffer
          ..writeln('Patrones de dificultad identificados:')
          ..writeln(poorAnalysis);
      }
    }

    // Add general analysis if no specific patterns found
    if (goodRules.isEmpty && poorRules.isEmpty) {
      buffer.writeln(
        'El análisis de $targetSubjectName muestra patrones complejos'
        ' en el rendimiento estudiantil.',
      );
    }

    return buffer.toString();
  }
}

// Alternative: Using collection package for more concise syntax
Map<PerformanceOutcome, List<RuleProcessed>> groupRulesByClassCondition(
  List<RuleProcessed> processedRules,
) {
  return processedRules.groupListsBy((rule) => rule.classCondition);
}

/// Processes rules that predict good performance
List<AnalysisMessage> processGoodConditions(
  List<RuleProcessed> goodRules,
  List<Subject> userApprovedSubjects,
  String targetSubjectName,
) {
  final messages = <AnalysisMessage>[];
  final goodSubjectsTaken = <String>{};
  final goodSubjectsNotTaken = <String>{};
  final poorSubjectsTaken = <String>{};

  final expandedRules = goodRules.expand((rule) => rule.conditions).toList();

  for (final rule in expandedRules) {
    final crossValidationResult = _crossValidateWithUser(
      condition: rule,
      approvedSubjects: userApprovedSubjects,
    );
    final subjectName = crossValidationResult.subjectName;

    // Skip unknown subjects
    if (subjectName == 'Unknown Subject') continue;

    // Analyze course taking patterns for good performance prediction
    if (rule.courseTakingPattern == CourseTakingPattern.taken) {
      // Student took this course early -
      //check if it correlates with good performance
      if (crossValidationResult.hasUserTakenSubject) {
        if (crossValidationResult.hasGoodPerformance) {
          goodSubjectsTaken.add(subjectName);
        } else {
          poorSubjectsTaken.add(subjectName);
        }
      } else {
        goodSubjectsNotTaken.add(subjectName);
      }
    } else if (rule.courseTakingPattern == CourseTakingPattern.notTaken) {
      // Student didn't take this course early -
      //check if this correlates with good performance
      if (crossValidationResult.hasUserTakenSubject) {
        if (crossValidationResult.hasGoodPerformance) {
          goodSubjectsTaken.add(subjectName);
        } else {
          poorSubjectsTaken.add(subjectName);
        }
      } else {
        goodSubjectsNotTaken.add(subjectName);
      }
    }
  }

  // Generate structured messages
  if (goodSubjectsTaken.isNotEmpty) {
    messages.add(
      AnalysisMessage(
        type: MessageType.success,
        title: 'Fortalezas Académicas',
        content:
            'Tienes altas probabilidades de aprobar $targetSubjectName gracias'
            ' a tu buen rendimiento previo en esta(s) asignatura(s):',
        subjects: goodSubjectsTaken.toList(),
      ),
    );
  }

  if (poorSubjectsTaken.isNotEmpty) {
    messages.add(
      AnalysisMessage(
        type: MessageType.warning,
        title: 'Debilidades Académicas',
        content: 'Considera reforzar estos conceptos '
            'antes de cursar $targetSubjectName.',
        subjects: poorSubjectsTaken.toList(),
      ),
    );
  }

  if (goodSubjectsNotTaken.isNotEmpty) {
    messages.add(
      AnalysisMessage(
        type: MessageType.info,
        title: 'Recomendación',
        content: 'Para asegurar un mejor desempeño en '
            '$targetSubjectName, es recomendable '
            'que realices previamente la(s) siguiente(s) asignatura(s):',
        subjects: goodSubjectsNotTaken.toList(),
      ),
    );
  }

  return messages;
}

/// Processes rules that predict poor performance
List<AnalysisMessage> processPoorConditions(
  List<RuleProcessed> poorRules,
  List<Subject> userApprovedSubjects,
  String targetSubjectName,
) {
  final messages = <AnalysisMessage>[];
  final poorSubjectsWithGoodPerformance = <String>{};
  final poorSubjectsWithPoorPerformance = <String>{};
  final poorSubjectsNotTaken = <String>{};

  final expandedRules = poorRules.expand((rule) => rule.conditions).toList();

  for (final rule in expandedRules) {
    final crossValidationResult = _crossValidateWithUser(
      condition: rule,
      approvedSubjects: userApprovedSubjects,
    );
    final subjectName = crossValidationResult.subjectName;

    // Skip unknown subjects
    if (subjectName == 'Unknown Subject') continue;

    // Analyze course taking patterns for poor performance prediction
    if (rule.courseTakingPattern == CourseTakingPattern.taken) {
      // Student took this course early - check
      //if it correlates with poor performance
      if (crossValidationResult.hasUserTakenSubject) {
        if (crossValidationResult.hasGoodPerformance) {
          poorSubjectsWithGoodPerformance.add(subjectName);
        } else {
          poorSubjectsWithPoorPerformance.add(subjectName);
        }
      } else {
        poorSubjectsNotTaken.add(subjectName);
      }
    } else if (rule.courseTakingPattern == CourseTakingPattern.notTaken) {
      // Student didn't take this course early - check
      // if this correlates with poor performance
      if (crossValidationResult.hasUserTakenSubject) {
        if (crossValidationResult.hasGoodPerformance) {
          poorSubjectsWithGoodPerformance.add(subjectName);
        } else {
          poorSubjectsWithPoorPerformance.add(subjectName);
        }
      } else {
        poorSubjectsNotTaken.add(subjectName);
      }
    }
  }

  // Generate structured messages
  if (poorSubjectsWithGoodPerformance.isNotEmpty) {
    messages.add(
      AnalysisMessage(
        type: MessageType.success,
        title: 'Recuperación Exitosa',
        content:
            'Tu rendimiento actual en las siguientes asignaturas sugiere que '
            'puedes superar los desafíos en $targetSubjectName.',
        subjects: poorSubjectsWithGoodPerformance.toList(),
      ),
    );
  }

  if (poorSubjectsWithPoorPerformance.isNotEmpty) {
    messages.add(
      AnalysisMessage(
        type: MessageType.warning,
        title: 'Preparación Necesaria',
        content: 'Es importante que te prepares especialmente '
            'para cursar $targetSubjectName. '
            'Considera reforzar los conceptos básicos relacionados '
            'antes de cursarlas.',
        subjects: poorSubjectsWithPoorPerformance.toList(),
      ),
    );
  }

  if (poorSubjectsNotTaken.isNotEmpty) {
    messages.add(
      AnalysisMessage(
        type: MessageType.error,
        title: 'Riesgo Potencial',
        content: 'Los patrones históricos sugieren que estas asignaturas '
            'pueden ser indicadores de dificultades en $targetSubjectName. '
            'Te recomendamos prepararte adecuadamente para estas asignaturas.',
        subjects: poorSubjectsNotTaken.toList(),
      ),
    );
  }

  return messages;
}

/// Cross-validates conditions with user's academic history
CrossValidationResult _crossValidateWithUser({
  required RuleCondition condition,
  required List<Subject> approvedSubjects,
}) {
  // Check if user has taken this subject (match by course ID)
  final baseCourseId = condition.subjectId.split('_').first;
  final takenSubject = approvedSubjects.firstWhereOrNull(
    (s) => s.code == baseCourseId,
  );

  // Determine if user had good performance (approved and no failed attempts)
  // ignore: avoid_bool_literals_in_conditional_expressions
  final hasGoodPerformance = takenSubject != null
      ? (takenSubject.isApproved && takenSubject.attempts == 0)
      : false;

  return CrossValidationResult(
    hasUserTakenSubject: takenSubject != null,
    hasGoodPerformance: hasGoodPerformance,
    subjectName: condition.subjectName,
  );
}

/// Merges rules that have the same classCondition by combining their conditions
List<RuleProcessed> _mergeRulesByClassCondition(List<RuleProcessed> rules) {
  final mergedRules = <PerformanceOutcome, RuleProcessed>{};

  for (final rule in rules) {
    // Filter out conditions with "Unknown Subject"
    final filteredConditions = rule.conditions
        .where((condition) => condition.subjectName != 'Unknown Subject')
        .toList();

    // Skip rules that have no valid conditions after filtering
    if (filteredConditions.isEmpty) continue;

    final filteredRule = rule.copyWith(conditions: filteredConditions);

    if (mergedRules.containsKey(rule.classCondition)) {
      // Merge conditions with existing rule
      final existingRule = mergedRules[rule.classCondition]!;
      final mergedConditions = [
        ...existingRule.conditions,
        ...filteredRule.conditions,
      ];

      mergedRules[rule.classCondition] = existingRule.copyWith(
        conditions: mergedConditions,
      );
    } else {
      // Create new rule
      mergedRules[rule.classCondition] = filteredRule;
    }
  }

  return mergedRules.values.toList();
}

/// Result of cross-validation with user data
class CrossValidationResult extends Equatable {
  const CrossValidationResult({
    required this.hasUserTakenSubject,
    required this.hasGoodPerformance,
    required this.subjectName,
  });
  final bool hasUserTakenSubject;
  final bool hasGoodPerformance;
  final String subjectName;

  @override
  List<Object?> get props =>
      [hasUserTakenSubject, hasGoodPerformance, subjectName];
}

class RuleProcessed extends Equatable {
  const RuleProcessed({
    required this.conditions,
    required this.classCondition,
    required this.classConditionName,
    this.confidence = 0.0,
  });

  factory RuleProcessed.fromString(
    String condition,
    List<PathSubject> subjects, {
    double confidence = 0.0,
  }) {
    // Split by comma to get individual conditions
    final parts = condition.split(', ');

    final conditions = <RuleCondition>[];
    PerformanceOutcome? classCondition;
    RuleCondition? classRule;

    for (final part in parts) {
      if (part.startsWith('class:')) {
        // Parse class condition: "class: 6415_1 > 2.5"
        final classPart = part.substring(6).trim(); // Remove "class: "
        classRule = RuleCondition.fromString(classPart, subjects);
        classCondition = ProcessedConditionParser.parsePerformanceOutcome(
          classRule.operator,
          classRule.threshold,
        );
      } else {
        // Parse regular condition: "7109_1 <= 0.5"
        conditions.add(RuleCondition.fromString(part, subjects));
      }
    }

    return RuleProcessed(
      conditions: conditions,
      classCondition:
          classCondition ?? PerformanceOutcome.poor, // Default fallback
      classConditionName: classRule != null
          ? subjects
                  .firstWhereOrNull(
                    (s) =>
                        s.id.toString() ==
                        classRule!.subjectId.split('_').first,
                  )
                  ?.name ??
              'Unknown Subject'
          : 'Unknown Subject',
      confidence: confidence,
    );
  }

  final List<RuleCondition> conditions;
  final PerformanceOutcome classCondition;
  final String classConditionName;
  final double confidence;

  @override
  List<Object?> get props =>
      [conditions, classCondition, classConditionName, confidence];

  RuleProcessed copyWith({
    List<RuleCondition>? conditions,
    PerformanceOutcome? classCondition,
    String? classConditionName,
    double? confidence,
  }) {
    return RuleProcessed(
      conditions: conditions ?? this.conditions,
      classCondition: classCondition ?? this.classCondition,
      classConditionName: classConditionName ?? this.classConditionName,
      confidence: confidence ?? this.confidence,
    );
  }
}

class RuleCondition extends Equatable {
  const RuleCondition({
    required this.subjectId,
    required this.operator,
    required this.threshold,
    required this.subjectName,
    required this.courseTakingPattern,
  });

  factory RuleCondition.fromString(
    String conditionString,
    List<PathSubject> subjects,
  ) {
    // Handle both formats: "7686_1 > 0.5" and "100 > 0.5"
    final regex = RegExp(r'(\d+(?:_\d+)?)\s*(<=|>|>=|<)\s*([\d.]+)');
    final match = regex.firstMatch(conditionString.trim());

    if (match == null) {
      throw FormatException('Invalid condition format: $conditionString');
    }
    // Extract base course ID (remove attempt suffix if present)
    final fullSubjectId = match.group(1)!; // e.g., "7686_1" or "100"
    final baseCourseId =
        fullSubjectId.split('_').first; // e.g., "7686" or "100"

    final subjectName = subjects
            .firstWhereOrNull(
              (subject) => subject.id.toString() == baseCourseId,
            )
            ?.name ??
        'Unknown Subject';

    final operator = match.group(2)!;
    final threshold = double.parse(match.group(3)!);
    final courseTakingPattern =
        ProcessedConditionParser.parseCourseTakingPattern(operator, threshold);

    return RuleCondition(
      subjectId: match.group(1)!, // "7686_1"
      subjectName: subjectName,
      operator: operator, // ">"
      threshold: threshold, // 0.5
      courseTakingPattern: courseTakingPattern,
    );
  }

  final String subjectId;
  final String operator;
  final double threshold;
  final String subjectName;
  final CourseTakingPattern courseTakingPattern;

  @override
  List<Object?> get props =>
      [subjectId, operator, threshold, subjectName, courseTakingPattern];
}

enum CourseTakingPattern {
  taken, // Course was taken in first attempt
  notTaken, // Course was not taken in first attempt
}

enum PerformanceOutcome {
  good, // Good performance (≤ 2.5)
  poor // Poor performance (> 2.5)
}

class ProcessedConditionParser {
  static CourseTakingPattern parseCourseTakingPattern(
    String operator,
    double threshold,
  ) {
    // Decision tree uses binary features: 0 = not taken, 1 = taken
    // Threshold 0.5 is the split point for binary classification

    if (operator == '<=' && threshold == 0.5) {
      return CourseTakingPattern.notTaken; // Course was NOT taken (0)
    } else if (operator == '>' && threshold == 0.5) {
      return CourseTakingPattern.taken; // Course was taken (1)
    } else {
      // Handle edge cases or different threshold values
      if (threshold < 0.5) {
        return CourseTakingPattern.notTaken;
      } else {
        return CourseTakingPattern.taken;
      }
    }
  }

  static PerformanceOutcome parsePerformanceOutcome(
    String operator,
    double threshold,
  ) {
    // Grade thresholds (≤ 2.5, > 2.5) only appear in the prediction part
    if (operator == '<=' && threshold <= 2.5) {
      return PerformanceOutcome.good; // Good performance
    } else if (operator == '>' && threshold > 2.5) {
      return PerformanceOutcome.poor; // Poor performance
    } else {
      // Default based on threshold
      if (threshold <= 2.5) {
        return PerformanceOutcome.good;
      } else {
        return PerformanceOutcome.poor;
      }
    }
  }
}
