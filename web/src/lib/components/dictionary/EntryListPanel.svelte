<script lang="ts">
    import type { DictionaryEntrySummary } from "$lib/ploverApi";
    import DictionaryMessage from "./DictionaryMessage.svelte";
    import type { EntryLoadState } from "./types";

    let {
        entryLoadState,
        entryLoadError,
        selectedDictionaryPath,
        entries,
        entryFilter,
        entryQuery,
        entryPageStart,
        entryPageEnd,
        entryTotalCount,
        hasPreviousPage,
        hasNextPage,
        deletingEntryKey,
        deleteError,
        onFilterChange,
        onApplyFilter,
        onPreviousPage,
        onNextPage,
        onDeleteEntry,
    }: {
        entryLoadState: EntryLoadState,
        entryLoadError: string | null,
        selectedDictionaryPath: string,
        entries: DictionaryEntrySummary[],
        entryFilter: string,
        entryQuery: string,
        entryPageStart: number,
        entryPageEnd: number,
        entryTotalCount: number,
        hasPreviousPage: boolean,
        hasNextPage: boolean,
        deletingEntryKey: string | null,
        deleteError: string | null,
        onFilterChange: (filter: string) => void,
        onApplyFilter: () => void,
        onPreviousPage: () => void,
        onNextPage: () => void,
        onDeleteEntry: (entry: DictionaryEntrySummary) => void | Promise<void>,
    } = $props();

    const applyFilter = (event: SubmitEvent) => {
        event.preventDefault();
        onApplyFilter();
    };
</script>

<section class="entries-panel" aria-labelledby="entries-title">
    <div class="section-heading">
        <div>
            <p class="eyebrow">Entries</p>
            <h2 id="entries-title">Entry list</h2>
        </div>

        <form class="filter-form" onsubmit={applyFilter}>
            <label class="filter-field">
                <span>Filter key/definition</span>
                <input
                    type="search"
                    value={entryFilter}
                    autocomplete="off"
                    oninput={(event) => onFilterChange(event.currentTarget.value)}
                />
            </label>

            <button type="submit" class="button secondary compact">
                Apply
            </button>
        </form>
    </div>

    {#if entryLoadState === "loading"}
        <DictionaryMessage>Loading entries</DictionaryMessage>
    {:else if entryLoadState === "error"}
        <DictionaryMessage variant="error">{entryLoadError}</DictionaryMessage>
    {:else if selectedDictionaryPath === ""}
        <DictionaryMessage>Select a dictionary</DictionaryMessage>
    {:else if entries.length === 0}
        <DictionaryMessage>No entries found</DictionaryMessage>
    {:else}
        <div class="entry-pagination" aria-live="polite">
            <span>
                Showing {entryPageStart}-{entryPageEnd} of {entryTotalCount}
                {#if entryQuery !== ""}
                    matching "{entryQuery}"
                {/if}
            </span>

            <div class="button-row">
                <button
                    type="button"
                    class="button secondary compact"
                    disabled={!hasPreviousPage}
                    onclick={onPreviousPage}
                >
                    Previous
                </button>

                <button
                    type="button"
                    class="button secondary compact"
                    disabled={!hasNextPage}
                    onclick={onNextPage}
                >
                    Next
                </button>
            </div>
        </div>

        <div class="entry-table" role="table" aria-label="Dictionary entries">
            <div class="entry-row heading" role="row">
                <span role="columnheader">Key</span>
                <span role="columnheader">Translation</span>
                <span role="columnheader">Definition</span>
                <span role="columnheader">Action</span>
            </div>

            {#each entries as entry (entry.key)}
                <div class="entry-row" role="row">
                    <span class="mono" role="cell">{entry.key}</span>
                    <span role="cell">{entry.translation ?? "Not resolved"}</span>
                    <span class="mono" role="cell">{entry.definition}</span>
                    <span role="cell">
                        <button
                            type="button"
                            class="button danger compact"
                            disabled={deletingEntryKey !== null}
                            aria-label={`Delete ${entry.key}`}
                            onclick={() => void onDeleteEntry(entry)}
                        >
                            {deletingEntryKey === entry.key ? "Deleting" : "Delete"}
                        </button>
                    </span>
                </div>
            {/each}
        </div>
    {/if}

    {#if deleteError !== null}
        <DictionaryMessage variant="error" live="polite">{deleteError}</DictionaryMessage>
    {/if}
</section>

<style lang="scss">
    @use "./dictionaryUi.scss" as ui;

    .entries-panel {
        @include ui.panel-surface;

        display: grid;
        gap: 1rem;

        min-width: 0;
        padding: 1rem;
    }

    .section-heading,
    .filter-form,
    .entry-pagination,
    .button-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .section-heading,
    .entry-pagination {
        justify-content: space-between;
    }

    .eyebrow {
        @include ui.eyebrow;
    }

    h2 {
        @include ui.h2;
    }

    .filter-form {
        width: min(26rem, 100%);
        justify-content: flex-end;
    }

    .filter-field {
        @include ui.field;

        width: min(18rem, 100%);
    }

    .filter-form .filter-field {
        flex: 1 1 14rem;
    }

    input {
        @include ui.form-control;

        height: 2.4rem;
        padding: 0 0.7rem;
    }

    .entry-pagination {
        min-width: 0;
        min-height: 2.25rem;
        color: oklch(0.38 0.03 165);
        font-size: 0.88rem;
        font-weight: 730;
    }

    .entry-pagination span {
        @include ui.truncated;
    }

    .button-row {
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .button {
        @include ui.button;
        @include ui.secondary-button;
        @include ui.danger-button;
        @include ui.compact-button;
    }

    .entry-table {
        display: grid;

        min-width: 0;
        overflow: auto;
        border: 0.0625rem solid oklch(0.86 0.014 160);
        border-radius: 0.375rem;
    }

    .entry-row {
        display: grid;
        grid-template-columns: minmax(8rem, 0.7fr) minmax(8rem, 0.8fr) minmax(18rem, 1.8fr) minmax(5.5rem, auto);
        align-items: center;
        gap: 0.75rem;

        min-width: 48rem;
        min-height: 2.75rem;
        padding: 0.5rem 0.65rem;
        border-bottom: 0.0625rem solid oklch(0.9 0.01 160);
        color: oklch(0.24 0.028 160);
        font-size: 0.9rem;
    }

    .entry-row:last-child {
        border-bottom: 0;
    }

    .entry-row.heading {
        min-height: 2.3rem;
        background: oklch(0.96 0.012 160);
        color: oklch(0.36 0.025 160);
        font-size: 0.78rem;
        font-weight: 760;
        text-transform: uppercase;
    }

    .entry-row span {
        @include ui.truncated;
    }

    .mono {
        @include ui.mono;
    }

    @media (max-width: 42rem) {
        .section-heading,
        .filter-form,
        .entry-pagination {
            align-items: stretch;
            flex-direction: column;
        }

        .filter-field,
        .filter-form {
            width: 100%;
        }

        .entry-pagination span {
            white-space: normal;
        }
    }
</style>
