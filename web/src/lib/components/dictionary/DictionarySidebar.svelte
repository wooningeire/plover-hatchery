<script lang="ts">
    import type { DictionarySummary } from "$lib/ploverApi";
    import DictionaryMessage from "./DictionaryMessage.svelte";
    import type { DictionaryLoadState } from "./types";

    let {
        loadState,
        loadError,
        dictionaries,
        selectedDictionaryPath,
        onSelect,
    }: {
        loadState: DictionaryLoadState,
        loadError: string | null,
        dictionaries: DictionarySummary[],
        selectedDictionaryPath: string,
        onSelect: (dictionaryPath: string) => void,
    } = $props();
</script>

<aside class="dictionary-list" aria-label="Loaded dictionaries">
    {#if loadState === "error"}
        <DictionaryMessage variant="error">{loadError}</DictionaryMessage>
    {:else if loadState === "loaded" && dictionaries.length === 0}
        <DictionaryMessage>No Hatchery dictionaries loaded</DictionaryMessage>
    {:else}
        {#each dictionaries as dictionary (dictionary.path)}
            <button
                type="button"
                class="dictionary-option"
                class:is-selected={dictionary.path === selectedDictionaryPath}
                onclick={() => onSelect(dictionary.path)}
            >
                <span>{dictionary.label}</span>
                <small title={dictionary.path}>{dictionary.path}</small>
            </button>
        {/each}
    {/if}
</aside>

<style lang="scss">
    @use "./dictionaryUi.scss" as ui;

    .dictionary-list {
        @include ui.panel-surface;

        display: grid;
        align-content: start;
        gap: 0.5rem;

        min-width: 0;
        padding: 0.75rem;
    }

    .dictionary-option {
        display: grid;
        gap: 0.25rem;

        width: 100%;
        min-width: 0;
        min-height: 3.75rem;
        padding: 0.65rem 0.7rem;
        border: 0.0625rem solid transparent;
        border-radius: 0.375rem;
        background: transparent;
        color: oklch(0.24 0.028 160);
        cursor: pointer;
        text-align: left;
    }

    .dictionary-option:hover,
    .dictionary-option.is-selected {
        border-color: oklch(0.78 0.055 170);
        background: oklch(0.95 0.02 170);
    }

    .dictionary-option span,
    .dictionary-option small {
        @include ui.truncated;
    }

    .dictionary-option span {
        font-weight: 760;
    }

    .dictionary-option small {
        @include ui.mono;

        color: oklch(0.45 0.024 165);
        font-size: 0.78rem;
    }

    @media (max-width: 58rem) {
        .dictionary-list {
            grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
        }
    }
</style>
