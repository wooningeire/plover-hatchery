<script lang="ts">
    import type { DictionaryStats } from "$lib/ploverApi";

    let {
        loadedCount,
        stats,
    }: {
        loadedCount: number,
        stats: DictionaryStats | null,
    } = $props();
</script>

<section class="stats-panel" aria-label="Dictionary stats">
    <article>
        <span>{loadedCount}</span>
        <small>Loaded</small>
    </article>

    <article>
        <span>{stats?.entryCount ?? 0}</span>
        <small>Entries</small>
    </article>

    <article>
        <span>{stats?.morphemeCount ?? 0}</span>
        <small>Morphemes</small>
    </article>

    <article>
        <span>{stats?.definitionCount ?? 0}</span>
        <small>Definitions</small>
    </article>
</section>

<style lang="scss">
    @use "./dictionaryUi.scss" as ui;

    .stats-panel {
        @include ui.panel-surface;

        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;

        min-width: 0;
        padding: 0.75rem;
    }

    .stats-panel article {
        display: grid;
        gap: 0.15rem;

        min-width: 0;
        padding: 0.75rem;
        border-radius: 0.375rem;
        background: oklch(0.96 0.018 200);
    }

    .stats-panel span {
        color: oklch(0.25 0.045 210);
        font-size: 1.35rem;
        font-weight: 790;
    }

    .stats-panel small {
        color: oklch(0.42 0.035 210);
        font-size: 0.78rem;
        font-weight: 730;
        text-transform: uppercase;
    }

    @media (max-width: 42rem) {
        .stats-panel {
            grid-template-columns: 1fr;
        }
    }
</style>
