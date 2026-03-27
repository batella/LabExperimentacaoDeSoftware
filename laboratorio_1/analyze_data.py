"""Script to analyze repository data and generate statistics for the report."""

import json
import statistics
from pathlib import Path
from collections import Counter
from datetime import datetime


def load_json_data(filepath):
    """Load repository data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_statistics(values):
    """Calculate statistical measures for a list of values."""
    if not values:
        return {}
    
    sorted_values = sorted(values)
    return {
        'median': statistics.median(values),
        'mean': statistics.mean(values),
        'min': min(values),
        'max': max(values),
        'q25': statistics.quantiles(values, n=4)[0] if len(values) > 1 else values[0],
        'q75': statistics.quantiles(values, n=4)[2] if len(values) > 1 else values[0],
    }


def analyze_repositories(data):
    """Analyze repository data and generate statistics."""
    
    # Extract metrics
    ages = [repo['ageInDays'] for repo in data]
    prs = [repo['pullRequests']['totalCount'] for repo in data]
    releases = [repo['releases']['totalCount'] for repo in data]
    days_since_update = [repo['daysSinceLastUpdate'] for repo in data]
    days_since_push = [repo['daysSinceLastPush'] for repo in data]
    closed_ratios = [repo['closedIssuesRatio'] for repo in data]
    
    # Languages
    languages = []
    for repo in data:
        if repo['primaryLanguage'] and repo['primaryLanguage']['name']:
            languages.append(repo['primaryLanguage']['name'])
        else:
            languages.append('None')
    
    language_counts = Counter(languages)
    
    # Calculate statistics
    results = {
        'total_repos': len(data),
        'rq01_age': calculate_statistics(ages),
        'rq02_prs': calculate_statistics(prs),
        'rq03_releases': calculate_statistics(releases),
        'rq04_days_since_update': calculate_statistics(days_since_update),
        'rq06_closed_ratio': calculate_statistics(closed_ratios),
        'rq05_languages': language_counts.most_common(),
    }
    
    # RQ06 - Distribution of closed issues ratio
    ratio_distribution = {
        'high': sum(1 for r in closed_ratios if r > 0.80),
        'medium_high': sum(1 for r in closed_ratios if 0.60 <= r <= 0.80),
        'medium_low': sum(1 for r in closed_ratios if 0.40 <= r < 0.60),
        'low': sum(1 for r in closed_ratios if r < 0.40),
    }
    results['rq06_distribution'] = ratio_distribution
    
    # Recent updates (last 30 days)
    recent_updates = sum(1 for d in days_since_update if d <= 30)
    results['recent_updates_30d'] = recent_updates
    
    return results


def analyze_by_language(data):
    """Analyze RQ02, RQ03, RQ04 metrics by programming language (RQ07)."""
    
    # Group by language
    by_language = {}
    for repo in data:
        lang = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else 'None'
        
        if lang not in by_language:
            by_language[lang] = {
                'prs': [],
                'releases': [],
                'days_since_update': []
            }
        
        by_language[lang]['prs'].append(repo['pullRequests']['totalCount'])
        by_language[lang]['releases'].append(repo['releases']['totalCount'])
        by_language[lang]['days_since_update'].append(repo['daysSinceLastUpdate'])
    
    # Calculate medians for each language
    language_analysis = {}
    for lang, metrics in by_language.items():
        if metrics['prs']:  # Only if there's data
            language_analysis[lang] = {
                'count': len(metrics['prs']),
                'median_prs': statistics.median(metrics['prs']),
                'median_releases': statistics.median(metrics['releases']),
                'median_days_since_update': statistics.median(metrics['days_since_update']),
            }
    
    # Sort by count
    sorted_langs = sorted(language_analysis.items(), key=lambda x: x[1]['count'], reverse=True)
    
    return sorted_langs


def print_report(results, lang_analysis):
    """Print formatted report."""
    
    print("=" * 80)
    print("ANÁLISE DE REPOSITÓRIOS POPULARES DO GITHUB")
    print("=" * 80)
    print(f"\nTotal de repositórios analisados: {results['total_repos']}")
    print(f"Data da análise: {datetime.now().strftime('%d/%m/%Y')}")
    
    # RQ01
    print("\n" + "-" * 80)
    print("RQ01 - IDADE DOS REPOSITÓRIOS")
    print("-" * 80)
    age = results['rq01_age']
    print(f"Mediana: {age['median']:.0f} dias (~{age['median']/365:.1f} anos)")
    print(f"Média: {age['mean']:.0f} dias (~{age['mean']/365:.1f} anos)")
    print(f"Mínimo: {age['min']} dias (~{age['min']/365:.1f} anos)")
    print(f"Máximo: {age['max']} dias (~{age['max']/365:.1f} anos)")
    print(f"Q1 (25%): {age['q25']:.0f} dias (~{age['q25']/365:.1f} anos)")
    print(f"Q3 (75%): {age['q75']:.0f} dias (~{age['q75']/365:.1f} anos)")
    
    # RQ02
    print("\n" + "-" * 80)
    print("RQ02 - PULL REQUESTS ACEITAS")
    print("-" * 80)
    prs = results['rq02_prs']
    print(f"Mediana: {prs['median']:.0f}")
    print(f"Média: {prs['mean']:.0f}")
    print(f"Mínimo: {prs['min']}")
    print(f"Máximo: {prs['max']}")
    print(f"Q1 (25%): {prs['q25']:.0f}")
    print(f"Q3 (75%): {prs['q75']:.0f}")
    
    # RQ03
    print("\n" + "-" * 80)
    print("RQ03 - RELEASES")
    print("-" * 80)
    rels = results['rq03_releases']
    print(f"Mediana: {rels['median']:.0f}")
    print(f"Média: {rels['mean']:.0f}")
    print(f"Mínimo: {rels['min']}")
    print(f"Máximo: {rels['max']}")
    print(f"Q1 (25%): {rels['q25']:.0f}")
    print(f"Q3 (75%): {rels['q75']:.0f}")
    
    # RQ04
    print("\n" + "-" * 80)
    print("RQ04 - DIAS DESDE ÚLTIMA ATUALIZAÇÃO")
    print("-" * 80)
    days = results['rq04_days_since_update']
    print(f"Mediana: {days['median']:.0f} dias")
    print(f"Média: {days['mean']:.0f} dias")
    print(f"Mínimo: {days['min']} dias")
    print(f"Máximo: {days['max']} dias")
    print(f"Q1 (25%): {days['q25']:.0f} dias")
    print(f"Q3 (75%): {days['q75']:.0f} dias")
    print(f"\nRepositórios atualizados nos últimos 30 dias: {results['recent_updates_30d']} ({results['recent_updates_30d']/results['total_repos']*100:.1f}%)")
    
    # RQ05
    print("\n" + "-" * 80)
    print("RQ05 - LINGUAGENS DE PROGRAMAÇÃO")
    print("-" * 80)
    print("\nTop 10 Linguagens:")
    for i, (lang, count) in enumerate(results['rq05_languages'][:10], 1):
        percentage = count / results['total_repos'] * 100
        print(f"{i:2d}. {lang:20s}: {count:4d} repositórios ({percentage:5.1f}%)")
    
    # RQ06
    print("\n" + "-" * 80)
    print("RQ06 - RAZÃO DE ISSUES FECHADAS")
    print("-" * 80)
    ratio = results['rq06_closed_ratio']
    print(f"Mediana: {ratio['median']:.2f} ({ratio['median']*100:.0f}%)")
    print(f"Média: {ratio['mean']:.2f} ({ratio['mean']*100:.0f}%)")
    print(f"Mínimo: {ratio['min']:.2f}")
    print(f"Máximo: {ratio['max']:.2f}")
    print(f"Q1 (25%): {ratio['q25']:.2f}")
    print(f"Q3 (75%): {ratio['q75']:.2f}")
    
    dist = results['rq06_distribution']
    total = results['total_repos']
    print(f"\nDistribuição:")
    print(f"  > 80% (alta):      {dist['high']:4d} repositórios ({dist['high']/total*100:.1f}%)")
    print(f"  60-80% (média):    {dist['medium_high']:4d} repositórios ({dist['medium_high']/total*100:.1f}%)")
    print(f"  40-60% (baixa):    {dist['medium_low']:4d} repositórios ({dist['medium_low']/total*100:.1f}%)")
    print(f"  < 40% (muito baixa): {dist['low']:4d} repositórios ({dist['low']/total*100:.1f}%)")
    
    # RQ07
    print("\n" + "-" * 80)
    print("RQ07 - ANÁLISE POR LINGUAGEM (BÔNUS)")
    print("-" * 80)
    print("\nTop 5 Linguagens:")
    print(f"\n{'Linguagem':<20} {'N':<6} {'PRs (med)':<12} {'Releases (med)':<15} {'Dias atualizaç (med)'}")
    print("-" * 80)
    for lang, stats in lang_analysis[:5]:
        print(f"{lang:<20} {stats['count']:<6} {stats['median_prs']:<12.0f} {stats['median_releases']:<15.0f} {stats['median_days_since_update']:.0f}")
    
    print("\n" + "=" * 80)


def main():
    """Main execution."""
    # Find the most recent JSON file
    output_dir = Path('output')
    json_files = sorted(output_dir.glob('repositories_*.json'))
    
    if not json_files:
        print("Nenhum arquivo JSON encontrado em output/")
        return
    
    # Use the most recent file
    latest_file = json_files[-1]
    print(f"Analisando: {latest_file.name}")
    print()
    
    # Load and analyze data
    data = load_json_data(latest_file)
    results = analyze_repositories(data)
    lang_analysis = analyze_by_language(data)
    
    # Print report
    print_report(results, lang_analysis)
    
    # Save results to file for reference
    output_file = output_dir / 'analysis_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        # Convert to serializable format
        export_data = {
            'file_analyzed': str(latest_file),
            'analysis_date': datetime.now().isoformat(),
            'results': results,
            'language_analysis': {lang: stats for lang, stats in lang_analysis}
        }
        # Handle Counter objects
        export_data['results']['rq05_languages'] = dict(results['rq05_languages'])
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nResultados salvos em: {output_file}")


if __name__ == "__main__":
    main()
