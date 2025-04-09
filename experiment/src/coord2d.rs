use ordered_float::{FloatIsNan, NotNan};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Coord2D {
    x: NotNan<f64>,
    y: NotNan<f64>,
}

impl Coord2D {
    pub fn new(x: f64, y: f64) -> Result<Self, FloatIsNan> {
        Ok(Self {
            x: NotNan::new(x)?,
            y: NotNan::new(y)?,
        })
    }

    pub fn distance(&self, other: &Self) -> Result<NotNan<f64>, FloatIsNan> {
        Ok(NotNan::new(f64::sqrt(
            (self.x - other.x).powi(2) + (self.y - other.y).powi(2),
        ))?)
    }

    pub fn translate(&mut self, other: &Self) {
        self.x += other.x;
        self.y += other.y;
    }

    pub fn to_bytes(self) -> [u8; 16] {
        let mut result: [u8; 16] = [0; 16];
        let (x_bytes, y_bytes) = result.split_at_mut(8);
        x_bytes.copy_from_slice(&self.x.to_be_bytes());
        y_bytes.copy_from_slice(&self.y.to_be_bytes());

        result
    }

    pub fn from_bytes(x_y: &[u8]) -> Self {
        if x_y.len() != 16 {
            panic!("Malformed serialized Coord2D")
        }

        let x = NotNan::new(f64::from_be_bytes(x_y[..8].try_into().unwrap())).unwrap();

        let y = NotNan::new(f64::from_be_bytes(x_y[8..].try_into().unwrap())).unwrap();

        Self { x, y }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_coord_2d_serde() {
        let x = Coord2D::new(-1.0, 2.0).unwrap();
        let bytes = x.clone().to_bytes();
        let rehydrated = Coord2D::from_bytes(&bytes);

        assert_eq!(x, rehydrated);
    }
}
