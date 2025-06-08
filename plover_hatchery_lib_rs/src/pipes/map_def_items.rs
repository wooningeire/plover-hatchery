use crate::defs::{
    Def, DefViewCursor, DefViewItemRef, Entity, Keysymbol, RawableEntity, Sopheme
};

use pyo3::{exceptions::PyException, prelude::*};


pub fn map_def<'a>(
    varname: &str,
    cur: &mut DefViewCursor<'a, '_>,
    handle_keysymbol: &impl Fn(&mut Vec<Keysymbol>, &Keysymbol, &mut DefViewCursor) -> Result<(), PyErr>,
) -> Result<Def, PyErr> {
    let mut new_def = Def::new(vec![], varname.to_string());

    let level = cur.stack.len() - 1;

    while let Some(child) = cur.stack[level].next(cur.view.defs()).map_err(PyException::new_err)? {
        if let Err(msg) = cur.step_in_at_start().unwrap() {
            return Err(PyException::new_err(msg));
        }

        new_def.rawables.push(match child {
            DefViewItemRef::Def(def) => RawableEntity::RawDef(map_def(&def.varname, cur, handle_keysymbol)?),

            DefViewItemRef::EntitySeq(_, varname) => RawableEntity::RawDef(map_def(&varname, cur, handle_keysymbol)?),

            DefViewItemRef::Sopheme(sopheme) => RawableEntity::Entity(Entity::Sopheme(map_sopheme(&sopheme.chars, cur, handle_keysymbol)?)),

            _ => return Err(PyException::new_err("malformed definition")),
        });

        cur.step_out();
    }

    Ok(new_def)
}


pub fn map_sopheme<'a>(
    chars: &str,
    cur: &mut DefViewCursor<'a, '_>,
    handle_keysymbol: &impl Fn(&mut Vec<Keysymbol>, &Keysymbol, &mut DefViewCursor) -> Result<(), PyErr>,
) -> Result<Sopheme, PyErr> {
    let mut new_sopheme = Sopheme::new(chars.to_string(), vec![]);

    let level = cur.stack.len() - 1;

    while let Some(child) = cur.stack[level].next(cur.view.defs()).map_err(PyException::new_err)? {
        if let Err(msg) = cur.step_in_at_start().unwrap() {
            return Err(PyException::new_err(msg));
        }

        match child {
            DefViewItemRef::Keysymbol(keysymbol) => handle_keysymbol(&mut new_sopheme.keysymbols, keysymbol, cur)?,

            _ => return Err(PyException::new_err("malformed definition")),
        };

        cur.step_out();
    }

    Ok(new_sopheme)
}