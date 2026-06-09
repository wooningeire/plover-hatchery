<script lang="ts">
    import type {
        DictionarySummary,
        SaveEntryResponse,
    } from "$lib/ploverApi";
    import DictionaryMessage from "./DictionaryMessage.svelte";
    import {
        breakdownHref,
        dictionaryLabel,
    } from "./format";
    import type {
        DictionaryLoadState,
        SaveState,
    } from "./types";

    let {
        dictionaries,
        selectedDictionary,
        selectedDictionaryPath,
        dictionaryLoadState,
        entryTranslation,
        entryDefinition,
        saveState,
        saveIsWorking,
        canSaveEntry,
        saveError,
        saveResult,
        onDictionaryChange,
        onTranslationChange,
        onDefinitionChange,
        onSave,
    }: {
        dictionaries: DictionarySummary[],
        selectedDictionary: DictionarySummary | null,
        selectedDictionaryPath: string,
        dictionaryLoadState: DictionaryLoadState,
        entryTranslation: string,
        entryDefinition: string,
        saveState: SaveState,
        saveIsWorking: boolean,
        canSaveEntry: boolean,
        saveError: string | null,
        saveResult: SaveEntryResponse | null,
        onDictionaryChange: (dictionaryPath: string) => void,
        onTranslationChange: (translation: string) => void,
        onDefinitionChange: (definition: string) => void,
        onSave: () => void | Promise<void>,
    } = $props();

    const submitEntry = (event: SubmitEvent) => {
        event.preventDefault();
        void onSave();
    };
</script>

<section class="entry-editor" aria-labelledby="entry-editor-title">
    <div class="section-heading">
        <div>
            <p class="eyebrow">Entry</p>
            <h2 id="entry-editor-title">Add entry</h2>
        </div>

        <div class="selected-path" title={selectedDictionary?.path ?? ""}>
            {selectedDictionary?.label ?? ""}
        </div>
    </div>

    <form class="entry-form" onsubmit={submitEntry}>
        <label class="field">
            <span>Dictionary</span>
            <select
                value={selectedDictionaryPath}
                disabled={dictionaryLoadState !== "loaded" || dictionaries.length === 0 || saveIsWorking}
                onchange={(event) => onDictionaryChange(event.currentTarget.value)}
            >
                {#each dictionaries as dictionary (dictionary.path)}
                    <option value={dictionary.path}>{dictionaryLabel(dictionary)}</option>
                {/each}
            </select>
        </label>

        <label class="field">
            <span>Translation</span>
            <input
                type="text"
                value={entryTranslation}
                disabled={saveIsWorking}
                autocomplete="off"
                oninput={(event) => onTranslationChange(event.currentTarget.value)}
            />
        </label>

        <label class="field full">
            <span>Definition</span>
            <textarea
                value={entryDefinition}
                disabled={saveIsWorking}
                rows="5"
                spellcheck="false"
                oninput={(event) => onDefinitionChange(event.currentTarget.value)}
            ></textarea>
        </label>

        <div class="form-actions">
            <button
                type="submit"
                class="button"
                disabled={!canSaveEntry}
            >
                {saveIsWorking ? "Saving" : "Save entry"}
            </button>
        </div>
    </form>

    {#if saveState === "saved" && saveResult !== null}
        <DictionaryMessage variant="success" live="polite">
            <span>Saved {saveResult.entry.key}</span>
            <a href={breakdownHref(saveResult.entry.translation)}>Open breakdown</a>
        </DictionaryMessage>
    {:else if saveState === "error"}
        <DictionaryMessage variant="error" live="polite">{saveError}</DictionaryMessage>
    {/if}
</section>

<style lang="scss">
    @use "./dictionaryUi.scss" as ui;

    .entry-editor {
        @include ui.panel-surface;

        display: grid;
        gap: 1rem;

        min-width: 0;
        padding: 1rem;
    }

    .section-heading,
    .form-actions {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
    }

    .eyebrow {
        @include ui.eyebrow;
    }

    h2 {
        @include ui.h2;
    }

    .selected-path {
        @include ui.truncated;
        @include ui.mono;

        color: oklch(0.45 0.024 165);
        font-size: 0.78rem;
    }

    .entry-form {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
    }

    .field {
        @include ui.field;
    }

    .field.full,
    .form-actions {
        grid-column: 1 / -1;
    }

    input,
    select,
    textarea {
        @include ui.form-control;
    }

    input,
    select {
        height: 2.4rem;
        padding: 0 0.7rem;
    }

    textarea {
        min-height: 8rem;
        padding: 0.7rem;
        resize: vertical;

        @include ui.mono;

        line-height: 1.45;
    }

    .button {
        @include ui.button;
    }

    @media (max-width: 42rem) {
        .section-heading,
        .form-actions {
            align-items: stretch;
            flex-direction: column;
        }

        .entry-form {
            grid-template-columns: 1fr;
        }
    }
</style>
