<script lang="ts">
    import type { CompileDictionaryResult } from "$lib/ploverApi";
    import {
        dictionaryLabel,
        dictionaryStatus,
    } from "./format";

    let {
        dictionaries,
    }: {
        dictionaries: CompileDictionaryResult[],
    } = $props();
</script>

<section class="compile-results" aria-label="Dictionary compile results">
    {#each dictionaries as dictionary}
        <article>
            <span title={dictionary.path}>{dictionaryLabel(dictionary)}</span>
            <small>{dictionaryStatus(dictionary)}</small>
        </article>
    {/each}
</section>

<style lang="scss">
    @use "./dictionaryUi.scss" as ui;

    .compile-results {
        @include ui.panel-surface;

        display: grid;
        gap: 0.5rem;

        min-width: 0;
        padding: 0.75rem;
    }

    .compile-results article {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.75rem;

        min-width: 0;
        min-height: 2.25rem;
        padding: 0.5rem 0.65rem;
        border: 0.0625rem solid oklch(0.88 0.012 160);
        border-radius: 0.375rem;
    }

    .compile-results span {
        @include ui.truncated;
        @include ui.mono;
    }

    .compile-results small {
        @include ui.truncated;
        @include ui.mono;

        color: oklch(0.45 0.024 165);
        font-size: 0.78rem;
        text-transform: capitalize;
    }
</style>
