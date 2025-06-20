use crate::defs::{
    Def, DefViewCursor, DefViewItemRef, Entity, Keysymbol, Sopheme, DefViewErr,
};

use pyo3::{exceptions::PyException, prelude::*};


pub fn map_def<'a>(
    varname: &str,
    cur: &mut DefViewCursor<'a, '_>,
    handle_keysymbol: &impl Fn(&mut Vec<Keysymbol>, &Keysymbol, &mut DefViewCursor) -> Result<(), PyErr>,
) -> Result<Def, PyErr> {
    let mut new_def = Def::new(vec![], varname.to_string());

    let level = cur.stack.len() - 1;

    while let Some(child) = cur.stack[level].next(cur.view.defs()).map_err(|err| err.as_pyerr())? {
        if !cur.step_in_at_start().map_err(|err| err.as_pyerr())? {
            return Err(DefViewErr::UnexpectedNone.as_pyerr());
        }

        new_def.entities.push(match child {
            DefViewItemRef::Def(def) => Entity::RawDef(map_def(&def.varname, cur, handle_keysymbol)?),

            DefViewItemRef::Entities(_, varname) => Entity::RawDef(map_def(&varname, cur, handle_keysymbol)?),

            DefViewItemRef::Sopheme(sopheme) => Entity::Sopheme(map_sopheme(&sopheme.chars, cur, handle_keysymbol)?),

            _ => return Err(DefViewErr::UnexpectedChildItemType.as_pyerr()),
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

    while let Some(child) = cur.stack[level].next(cur.view.defs()).map_err(|err| err.as_pyerr())? {
        if !cur.step_in_at_start().map_err(|err| err.as_pyerr())? {
            return Err(DefViewErr::UnexpectedNone.as_pyerr());
        }

        match child {
            DefViewItemRef::Keysymbol(keysymbol) => handle_keysymbol(&mut new_sopheme.keysymbols, keysymbol, cur)?,

            _ => return Err(PyException::new_err(DefViewErr::UnexpectedChildItemType.as_pyerr())),
        };

        cur.step_out();
    }

    Ok(new_sopheme)
}


fn foreach_entity<'a>(
    cur: &mut DefViewCursor<'a, '_>,
    handle_item: &impl Fn(&mut DefViewCursor) -> Result<(), DefViewErr>,
) -> Result<(), DefViewErr> {
    handle_item(cur)?;

    let level = cur.stack.len() - 1;

    while let Some(_) = cur.stack[level].next(cur.view.defs())? {
        if !cur.step_in_at_start()? {
            return Err(DefViewErr::UnexpectedNone);
        }

        foreach_entity(cur, handle_item)?;

        cur.step_out();
    }

    Ok(())
}
