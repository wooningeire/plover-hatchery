pub struct BinaryWriter {
    bytes: Vec<u8>,
}

impl BinaryWriter {
    pub fn new() -> Self {
        Self { bytes: Vec::new() }
    }

    pub fn into_bytes(self) -> Vec<u8> {
        self.bytes
    }

    pub fn write_magic(&mut self, magic: &[u8]) {
        self.bytes.extend_from_slice(magic);
    }

    #[inline]
    pub fn write_u64(&mut self, value: u64) {
        let mut value = value;
        while value >= 0x80 {
            self.bytes.push((value as u8) | 0x80);
            value >>= 7;
        }
        self.bytes.push(value as u8);
    }

    #[inline]
    pub fn write_usize(&mut self, value: usize) {
        self.write_u64(value as u64);
    }

    #[inline]
    pub fn write_option_usize(&mut self, value: Option<usize>) {
        match value {
            Some(value) => {
                self.bytes.push(1);
                self.write_usize(value);
            }
            None => self.bytes.push(0),
        }
    }

    #[inline]
    pub fn write_f64(&mut self, value: f64) {
        self.bytes.extend_from_slice(&value.to_le_bytes());
    }

    pub fn write_usize_slice(&mut self, values: &[usize]) {
        self.write_usize(values.len());
        for value in values {
            self.write_usize(*value);
        }
    }

    pub fn write_string(&mut self, value: &str) {
        let bytes = value.as_bytes();
        self.write_usize(bytes.len());
        self.bytes.extend_from_slice(bytes);
    }
}

pub struct BinaryReader<'a> {
    bytes: &'a [u8],
    offset: usize,
}

impl<'a> BinaryReader<'a> {
    pub fn new(bytes: &'a [u8]) -> Self {
        Self { bytes, offset: 0 }
    }

    pub fn finish(&self) -> Result<(), String> {
        if self.offset == self.bytes.len() {
            Ok(())
        } else {
            Err(format!(
                "cache has {} trailing bytes",
                self.bytes.len() - self.offset
            ))
        }
    }

    pub fn read_magic(&mut self, magic: &[u8]) -> Result<(), String> {
        let found = self.read_exact(magic.len())?;
        if found == magic {
            Ok(())
        } else {
            Err("cache magic does not match".to_string())
        }
    }

    #[inline]
    pub fn read_u8(&mut self) -> Result<u8, String> {
        if self.offset >= self.bytes.len() {
            return Err("cache ended early".to_string());
        }

        let byte = self.bytes[self.offset];
        self.offset += 1;
        Ok(byte)
    }

    #[inline]
    pub fn read_u64(&mut self) -> Result<u64, String> {
        let mut value = 0_u64;
        let mut shift = 0;
        let mut offset = self.offset;

        for _ in 0..10 {
            if offset >= self.bytes.len() {
                return Err("cache ended early".to_string());
            }

            let byte = self.bytes[offset];
            offset += 1;
            value |= u64::from(byte & 0x7f) << shift;
            if byte & 0x80 == 0 {
                self.offset = offset;
                return Ok(value);
            }
            shift += 7;
        }

        Err("cache varint is too long".to_string())
    }

    #[inline]
    pub fn read_usize(&mut self) -> Result<usize, String> {
        usize::try_from(self.read_u64()?).map_err(|_| "cache integer is too large".to_string())
    }

    #[inline]
    pub fn read_option_usize(&mut self) -> Result<Option<usize>, String> {
        match self.read_u8()? {
            0 => Ok(None),
            1 => Ok(Some(self.read_usize()?)),
            _ => Err("cache option tag is invalid".to_string()),
        }
    }

    pub fn read_f64(&mut self) -> Result<f64, String> {
        let end = self
            .offset
            .checked_add(8)
            .ok_or_else(|| "cache offset overflowed".to_string())?;
        if end > self.bytes.len() {
            return Err("cache ended early".to_string());
        }

        let bytes = &self.bytes[self.offset..end];
        self.offset = end;
        let mut array = [0; 8];
        array.copy_from_slice(bytes);
        Ok(f64::from_le_bytes(array))
    }

    pub fn read_usize_vec(&mut self) -> Result<Vec<usize>, String> {
        let len = self.read_usize()?;
        let mut values = Vec::with_capacity(len);
        for _ in 0..len {
            values.push(self.read_usize()?);
        }
        Ok(values)
    }

    pub fn read_string(&mut self) -> Result<String, String> {
        let len = self.read_usize()?;
        let bytes = self.read_exact(len)?;
        String::from_utf8(bytes.to_vec()).map_err(|_| "cache string is not valid UTF-8".to_string())
    }

    fn read_exact(&mut self, len: usize) -> Result<&'a [u8], String> {
        let end = self
            .offset
            .checked_add(len)
            .ok_or_else(|| "cache offset overflowed".to_string())?;
        if end > self.bytes.len() {
            return Err("cache ended early".to_string());
        }

        let slice = &self.bytes[self.offset..end];
        self.offset = end;
        Ok(slice)
    }
}
