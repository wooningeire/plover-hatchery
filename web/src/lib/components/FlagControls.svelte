<script lang="ts">
    export interface FlagSettings {
        opacity: number;
        strokeWidth: number;
        dashed: boolean;
        dashLength: number;
    }

    interface Props {
        flags: string[];
        settings: Record<string, FlagSettings>;
    }

    let { flags, settings = $bindable() }: Props = $props();
</script>

<div class="controls">
    <h3>Transition Flags</h3>
    {#if flags.length === 0}
        <div class="empty">No flags found</div>
    {/if}
    {#each flags as flag}
        <div class="flag-control">
            <span class="flag-name">{flag}</span>
            <div class="control-row">
                <label class="opacity-control">
                    Opacity
                    <input 
                        type="range" 
                        min="0" 
                        max="1" 
                        step={Number.EPSILON} 
                        bind:value={settings[flag].opacity} 
                    />
                    <span class="value">{settings[flag].opacity.toFixed(2)}</span>
                </label>
                <label class="stroke-width-control">
                    Width
                    <input 
                        type="range" 
                        min="0.1" 
                        max="30" 
                        step={Number.EPSILON} 
                        bind:value={settings[flag].strokeWidth} 
                    />
                    <span class="value">{settings[flag].strokeWidth}</span>
                </label>
                <label class="dashed-control">
                    <input 
                        type="checkbox" 
                        bind:checked={settings[flag].dashed} 
                    />
                    Dashed
                </label>
                {#if settings[flag].dashed}
                    <label class="dash-length-control">
                        Dash
                        <input 
                            type="range" 
                            min="0.1" 
                            max="100" 
                            step={Number.EPSILON} 
                            bind:value={settings[flag].dashLength} 
                        />
                        <span class="value">{settings[flag].dashLength}</span>
                    </label>
                {/if}
            </div>
        </div>
    {/each}
</div>

<style>
    .controls {
        margin-bottom: 1rem;
        padding: 1rem;
        background: #f9f9f9;
        border: 1px solid #eee;
        border-radius: 4px;
        max-height: 300px;
        overflow-y: auto;
    }
    .flag-control {
        margin-bottom: 0.75rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #eee;
    }
    .flag-control:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    .flag-name {
        font-weight: 600;
        display: block;
        margin-bottom: 0.5rem;
    }
    .control-row {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: center;
    }
    .opacity-control,
    .stroke-width-control,
    .dash-length-control {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .dashed-control {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        cursor: pointer;
    }
    .value {
        min-width: 2.5rem;
        text-align: right;
        font-variant-numeric: tabular-nums;
        color: #666;
        font-size: 0.875rem;
    }
    input[type="range"] {
        width: 100px;
        cursor: pointer;
    }
    input[type="checkbox"] {
        cursor: pointer;
    }
    .empty {
        color: #666;
        font-style: italic;
    }
</style>
