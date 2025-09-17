// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'subject.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Subject _$SubjectFromJson(Map<String, dynamic> json) => Subject(
      code: json['code'] as String,
      name: json['name'] as String,
      semester: json['semester'] as String,
      date: Subject._dateTimeFromCustomFormat(json['date'] as String?),
      status: json['status'] as String,
      grade: (json['grade'] as num?)?.toInt(),
      attempts: (json['attempts'] as num?)?.toInt() ?? 0,
      lastAttemptDate: Subject._dateTimeFromCustomFormat(
        json['last_attempt_date'] as String?,
      ),
      resultType: json['result_type'] as String?,
    );

Map<String, dynamic> _$SubjectToJson(Subject instance) => <String, dynamic>{
      'code': instance.code,
      'name': instance.name,
      'semester': instance.semester,
      'date': Subject._dateTimeToCustomFormat(instance.date),
      'status': instance.status,
      'grade': instance.grade,
      'attempts': instance.attempts,
      'last_attempt_date':
          Subject._dateTimeToCustomFormat(instance.lastAttemptDate),
      'result_type': instance.resultType,
    };
