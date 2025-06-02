// use super::{
//     Def, DefRefCursor, OverridableEntity, Sopheme
// };


// pub struct DefSophemesIter<'a> {
//     def: &'a Def,
//     cursor: DefRefCursor<'a>,
// }

// impl<'a> DefSophemesIter<'a> {
//     pub fn new(def: &'a Def) -> DefSophemesIter<'a> {
//         DefSophemesIter {
//             cursor: DefRefCursor::initial(def),
//             def,
//         }
//     }
// }

// impl<'a> Iterator for DefSophemesIter<'a> {
//     type Item = &'a Sopheme;

//     fn next(&mut self) -> Option<Self::Item> {
//         loop {
//             match self.cursor.cur_tip_item() {
//                 Some(overridable_entity) => match overridable_entity {
                    
//                 },
//                 None => return None,
//             }
//         }
//     }
// }


// pub struct KeysymbolsIter<'a> {
//     cursor: DefRefCursor<'a>,
// }

// impl<'a> KeysymbolsIter<'a> {
//     pub fn new(definition: &'a Def) -> KeysymbolsIter<'a> {
//         KeysymbolsIter {
//             cursor: DefRefCursor::initial(definition),
//         }
//     }

//     fn next(&mut self) -> bool {
//         self.cursor.step

//         match self.cursor.current_keysymbol() {
//             Some(keysymbol) => {
//                 self.cursor.move_to_next_keysymbol();

//                 true
//             },

//             None => false,
//         }
//     }
// }