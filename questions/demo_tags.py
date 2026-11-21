from itertools import chain, count, product

from .models import Tag


TECHNOLOGIES = (
    'python', 'django', 'postgresql', 'javascript', 'typescript', 'html',
    'css', 'docker', 'git', 'linux', 'sql', 'rest-api', 'bootstrap',
    'fastapi', 'flask', 'vue', 'react', 'node.js', 'pytest', 'redis',
    'mysql', 'sqlite', 'nginx', 'kubernetes', 'java', 'kotlin', 'php',
    'go', 'rust', 'c++', 'c#', 'dotnet', 'spring', 'laravel', 'svelte', 'next.js',
)

TOPICS = (
    'setup', 'config', 'updates', 'compatibility', 'dependencies', 'build',
    'deployment', 'debugging', 'testing', 'errors', 'logging', 'monitoring',
    'performance', 'profiling', 'security', 'networking', 'time-outs',
    'memory', 'documentation', 'automation', 'ci', 'development',
)

DETAILS = (
    'examples', 'troubleshooting', 'tools', 'best-practices', 'integration',
    'local', 'production', 'windows', 'linux', 'macos', 'docker',
    'configuration', 'migration',
)


def demo_tag_candidates():
    yield from TECHNOLOGIES
    yield from (f'{tech}-{topic}' for tech, topic in product(TECHNOLOGIES, TOPICS))
    for detail in chain(DETAILS, map(str, count(2))):
        yield from (
            f'{tech}-{topic}-{detail}'
            for tech, topic in product(TECHNOLOGIES, TOPICS)
        )


def available_demo_tag_names():
    used_names = set(Tag.objects.values_list('name', flat=True))
    for name in demo_tag_candidates():
        if name not in used_names:
            used_names.add(name)
            yield name
