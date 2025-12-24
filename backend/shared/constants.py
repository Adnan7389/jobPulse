# Shared constants for job categories, work modes, and job types.

JOB_CATEGORIES = [
    ('software', 'Software Development'),
    ('marketing', 'Marketing'),
    ('design', 'Design'),
    ('sales', 'Sales'),
    ('finance', 'Finance'),
    ('hr', 'Human Resources'),
    ('customer_service', 'Customer Service'),
    ('management', 'Management'),
    ('other', 'Other'),
]

WORK_MODES = [
    ('remote', 'Remote'),
    ('hybrid', 'Hybrid'),
    ('onsite', 'On-site'),
]

USER_WORK_MODES = WORK_MODES + [('all', 'Any / All')]

JOB_TYPES = [
    ('full_time', 'Full-time'),
    ('part_time', 'Part-time'),
]

USER_JOB_TYPES = JOB_TYPES + [('all', 'Any / All')]
