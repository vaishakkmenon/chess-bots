pub fn enumerate_subsets<F>(mask: u64, mut f: F)
where
    F: FnMut(u64),
{
    let mut subset = mask;
    loop {
        f(subset);
        if subset == 0 {
            break;
        }
        subset = (subset - 1) & mask;
    }
}
