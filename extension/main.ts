import {exists} from "jsr:@std/fs/exists";
import {parse} from "@eemeli/yaml";

if (await exists(`./out/`)) {
    await Deno.remove(`./out/`, { recursive: true });
}
await Deno.mkdir(`./out/`, { recursive: true });

const promises: Promise<void>[] = [];

for await (const entry of Deno.readDir("./syntaxes/")) {
    if (!entry.name.endsWith(".yaml")) continue;

    promises.push((async () => {
        const filename = entry.name.slice(0, -5);
        const grammarYaml = new TextDecoder().decode(await Deno.readFile(`./syntaxes/${filename}.yaml`));
        const grammar = parse(grammarYaml);
        const grammarJson = JSON.stringify(grammar);
        await Deno.writeFile(`./out/${filename}.json`, new TextEncoder().encode(grammarJson));
    })());
}

await Promise.all(promises);

