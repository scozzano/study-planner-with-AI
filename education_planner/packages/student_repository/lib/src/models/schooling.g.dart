// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'schooling.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Schooling _$SchoolingFromJson(Map<String, dynamic> json) => Schooling(
      id: json['id'] as String?,
      name: json['name'] as String?,
      document: json['document'] as String?,
      enrollmentNumber: json['enrollment_number'] as String?,
      title: json['title'] as String?,
      plan: json['plan'] as String?,
      startDate:
          Schooling._dateTimeFromCustomFormat(json['start_date'] as String?),
      averageGrade: (json['average_grade'] as num).toInt(),
      averageApprovedGrade: (json['average_approved_grade'] as num).toInt(),
      subjectsRequired: (json['subjects_required'] as num).toInt(),
      subjectsObtained: (json['subjects_obtained'] as num).toInt(),
      failedSubjects: (json['failed_subjects'] as num).toInt(),
      subjects: (json['subjects'] as List<dynamic>)
          .map((e) => Subject.fromJson(e as Map<String, dynamic>))
          .toList(),
      graduationDate: Schooling._dateTimeFromCustomFormat(
        json['graduation_date'] as String?,
      ),
    );

Map<String, dynamic> _$SchoolingToJson(Schooling instance) => <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'document': instance.document,
      'enrollment_number': instance.enrollmentNumber,
      'title': instance.title,
      'plan': instance.plan,
      'start_date': Schooling._dateTimeToCustomFormat(instance.startDate),
      'graduation_date':
          Schooling._dateTimeToCustomFormat(instance.graduationDate),
      'average_grade': instance.averageGrade,
      'average_approved_grade': instance.averageApprovedGrade,
      'subjects_required': instance.subjectsRequired,
      'subjects_obtained': instance.subjectsObtained,
      'failed_subjects': instance.failedSubjects,
      'subjects': instance.subjects.map((e) => e.toJson()).toList(),
    };
